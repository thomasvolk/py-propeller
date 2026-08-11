from propeller.errors import PropellerValidationError
from propeller.notes import PitchBend, Rest, Slide

PPQN: int = 480


def _beats_to_ticks(beats: float, denominator: int = 4) -> int:
    return round(beats * PPQN * 4 / denominator)


def _pb_to_int(value: float) -> int:
    return int(round((value + 1.0) / 2.0 * 16383))


def _slide_interval_tick_lengths(tone_widths: list[float], total_duration_ticks: int) -> list[int]:
    """Split total_duration_ticks across intervals proportional to their tone_width.

    Uses cumulative-boundary rounding so the lengths always sum exactly to
    total_duration_ticks (no drift from independently rounding each share).
    """
    total_width = sum(tone_widths)
    lengths = []
    prev_boundary = 0
    cumulative = 0.0
    for width in tone_widths:
        cumulative += width
        boundary = round(total_duration_ticks * cumulative / total_width)
        lengths.append(boundary - prev_boundary)
        prev_boundary = boundary
    return lengths


def _slide_pitch_bend_values(tone_width: float, steps: float, ascending: bool = True) -> list[float]:
    """Evenly-spaced PitchBend values from 0 up to tone_width (F-6, F-7), in
    increments no larger than steps when it divides evenly. The event count
    is rounded to the nearest whole number when it doesn't (F-10), so the
    actual increment can exceed steps in that case rather than raising."""
    count = max(1, round(tone_width / steps))
    sign = 1.0 if ascending else -1.0
    return [sign * tone_width * j / count for j in range(1, count + 1)]


def _slide_note_rows(slide, start_tick: int, denominator: int = 4) -> list:
    """One retriggered Note row per Slide interval, at that interval's start
    pitch, using the Slide's start-note velocity (F-5, F-9)."""
    intervals = slide.intervals()
    total_duration_ticks = _beats_to_ticks(slide.duration, denominator)
    tone_widths = [i.tone_width for i in intervals]
    interval_lengths = _slide_interval_tick_lengths(tone_widths, total_duration_ticks)
    rows = []
    tick = start_tick
    for interval, length in zip(intervals, interval_lengths):
        rows.append([tick, length, interval.start_pitch, slide.start.velocity])
        tick += length
    return rows


def _expand_slide(slide, start_tick: int, denominator: int = 4) -> tuple[list, list, int]:
    """Expand a Slide into its retriggered Note rows and PitchBend rows,
    atomically, as if it were a single larger Note (D-1 option A).

    Returns (note_rows, pitch_bend_rows, total_duration_ticks) so the caller
    can extend its accumulators and advance the shared tick cursor once.
    """
    total_duration_ticks = _beats_to_ticks(slide.duration, denominator)
    notes_out = _slide_note_rows(slide, start_tick, denominator)
    ascending = slide.end.pitch > slide.start.pitch
    pitch_bends_out = []
    for interval, note_row in zip(slide.intervals(), notes_out):
        interval_tick, interval_length = note_row[0], note_row[1]
        values = _slide_pitch_bend_values(interval.tone_width, slide.steps, ascending)
        count = len(values)
        for j, value in enumerate(values, start=1):
            pb_tick = interval_tick + round(interval_length * j / count)
            pitch_bends_out.append([pb_tick, _pb_to_int(value)])
    return notes_out, pitch_bends_out, total_duration_ticks


def _serialize_lane(
    lane,
    denominator: int = 4,
    emit_trailing_pb: bool = False,
    tag_source: bool = False,
) -> tuple[list, list]:
    """Serialize a single lane into (notes_out, pitch_bends_out).

    ``tag_source`` controls the shape of each pitch_bends_out element:
    - False (default, unchanged from pre-EP-2 behaviour): ``[tick, value]``
      pairs. Preserved so that pre-existing direct callers of this function
      (and their tests) keep working unmodified.
    - True: ``(tick, value, source)`` triples, where ``source`` is
      ``'manual'`` for a row flushed from a literal PitchBend item (both the
      note-triggered and trailing flush) and ``'slide'`` for rows produced by
      ``_expand_slide``. Used by ``_serialize_track``'s multi-lane branch to
      drive EP-2 concurrent-Slide consolidation.
    """

    def _emit_manual_pb(tick, value):
        if tag_source:
            pitch_bends_out.append((tick, _pb_to_int(value), 'manual'))
        else:
            pitch_bends_out.append([tick, _pb_to_int(value)])

    tick_cursor = 0
    notes_out = []
    pitch_bends_out = []
    pending_pb_value: float | None = None
    pending_pb_tick: int = 0
    for item in lane:
        if isinstance(item, PitchBend):
            if pending_pb_value is not None:
                _emit_manual_pb(pending_pb_tick, pending_pb_value)
            pending_pb_value = item.value
            pending_pb_tick = tick_cursor
            continue
        if isinstance(item, Slide):
            if pending_pb_value is not None:
                _emit_manual_pb(pending_pb_tick, pending_pb_value)
                pending_pb_value = None
            slide_notes, slide_pitch_bends, slide_ticks = _expand_slide(
                item, tick_cursor, denominator
            )
            notes_out.extend(slide_notes)
            if tag_source:
                pitch_bends_out.extend(
                    (pb_tick, pb_value, 'slide') for pb_tick, pb_value in slide_pitch_bends
                )
            else:
                pitch_bends_out.extend(slide_pitch_bends)
            tick_cursor += slide_ticks
            continue
        duration_ticks = _beats_to_ticks(item.duration, denominator)
        if isinstance(item, Rest):
            tick_cursor += duration_ticks
        else:
            if pending_pb_value is not None:
                _emit_manual_pb(pending_pb_tick, pending_pb_value)
                pending_pb_value = None
            notes_out.append([tick_cursor, duration_ticks, item.pitch, item.velocity])
            tick_cursor += duration_ticks
    if emit_trailing_pb and pending_pb_value is not None:
        _emit_manual_pb(pending_pb_tick, pending_pb_value)
    return notes_out, pitch_bends_out


def _consolidate_pitch_bends(rows: list) -> list:
    """Consolidate (tick, value, source) rows from all of a track's lanes
    into the final [tick, value] pitch-bends list (EP-2 F-1/F-4/F-5/F-6).

    - A tick with exactly one contributing row passes through unchanged.
    - A tick with more than one row collapses to a single [tick, value] row
      only if every row at that tick has source == 'slide' and all of their
      values agree.
    - Otherwise (any row is 'manual', or two-or-more 'slide' rows disagree
      on value) the whole serialization is invalid.

    Grouping uses an order-preserving dict keyed by tick, and the result is
    sorted by tick before being returned, so the output is deterministic
    across repeated calls for the same input (NF-1).
    """
    by_tick: dict[int, list] = {}
    for tick, value, source in rows:
        by_tick.setdefault(tick, []).append((value, source))

    result = []
    for tick, entries in by_tick.items():
        if len(entries) == 1:
            value, _source = entries[0]
            result.append([tick, value])
            continue
        values = {value for value, _source in entries}
        sources = {source for _value, source in entries}
        if sources == {'slide'} and len(values) == 1:
            result.append([tick, entries[0][0]])
        else:
            raise PropellerValidationError(
                'multiple lanes produce a pitch bend at the same tick offset'
            )
    return sorted(result, key=lambda pb: pb[0])


def _serialize_track(track, denominator: int = 4) -> dict:
    notes = track.notes
    if notes and isinstance(notes[0], list):
        all_notes = []
        all_pb_rows = []
        for lane in notes:
            lane_notes, lane_pbs = _serialize_lane(
                lane, denominator, emit_trailing_pb=True, tag_source=True
            )
            all_notes.extend(lane_notes)
            all_pb_rows.extend(lane_pbs)
        notes_out = sorted(all_notes, key=lambda n: n[0])
        pitch_bends_out = _consolidate_pitch_bends(all_pb_rows)
    else:
        notes_out, pitch_bends_out = _serialize_lane(notes, denominator)
    result = {
        'name': track.name,
        'channel': track.channel,
        'instrument': track.instrument,
        'notes': notes_out,
    }
    if pitch_bends_out:
        result['pitch-bends'] = pitch_bends_out
    return result


def serialize(project) -> dict:
    numerator, denominator = project.time_signature
    loop_duration = round(project.bars * numerator * PPQN * 4 / denominator)
    return {
        'header': {
            'bpm': project.bpm,
            'loop_duration': loop_duration,
        },
        'tracks': [_serialize_track(t, denominator) for t in project.tracks],
    }
