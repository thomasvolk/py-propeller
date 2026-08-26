from typing import Callable

from propeller.errors import PropellerValidationError
from propeller.notes import PitchBend, Rest, Slide
from propeller.notes.Slide import SlideCurve, SlideTarget

PPQN: int = 480


def _beats_to_ticks(beats: float, denominator: int = 4) -> int:
    return round(beats * PPQN * 4 / denominator)


def _pb_to_int(value: float) -> int:
    return int(round((value + 1.0) / 2.0 * 16383))


def _clip(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _target_value_at(target) -> Callable[[float], float]:
    if isinstance(target, (SlideTarget, SlideCurve)):
        return target.value_at
    return target


def _target_steps(target) -> float:
    if isinstance(target, (SlideTarget, SlideCurve)):
        return target.steps
    return 0.01


def _slide_pitch_bend_values(value_at, steps: float) -> list[float]:
    """Evenly-spaced PitchBend values sampled from value_at(progress) at
    progress = j/count for j in 1..count, where count = round(1/steps).
    Each sampled value is clipped to the valid pitch-bend range
    [-1.0, 1.0]."""
    count = max(1, round(1 / steps))
    return [_clip(value_at(j / count)) for j in range(1, count + 1)]


def _expand_slide(slide, start_tick: int, denominator: int = 4) -> tuple[list, list, int]:
    """Expand a Slide into its single Note row and a ramp of PitchBend rows,
    atomically.

    The pitch bend is reset to zero at the slide's note-on (so it always
    starts its ramp from center, regardless of what preceded it) and again
    at the slide's end tick (so a bend never leaks into whatever plays
    next). The final ramp step always lands exactly on the end tick too
    (it's simultaneous with the note's note-off), so the zero reset
    replaces it there rather than adding a conflicting duplicate.

    Returns (note_rows, pitch_bend_rows, total_duration_ticks) so the caller
    can extend its accumulators and advance the shared tick cursor once.
    """
    total_duration_ticks = _beats_to_ticks(slide.duration, denominator)
    end_tick = start_tick + total_duration_ticks
    notes_out = [[start_tick, total_duration_ticks, slide.start.pitch, slide.start.velocity]]
    values = _slide_pitch_bend_values(_target_value_at(slide.target), _target_steps(slide.target))
    count = len(values)
    pitch_bends_out = [[start_tick, _pb_to_int(0.0)]]
    for j, value in enumerate(values, start=1):
        pb_tick = start_tick + round(total_duration_ticks * j / count)
        pitch_bends_out.append([pb_tick, _pb_to_int(value)])
    pitch_bends_out[-1] = [end_tick, _pb_to_int(0.0)]
    return notes_out, pitch_bends_out, total_duration_ticks


def _dedup_same_tick(rows: list) -> list:
    """Keep only the first pitch-bend row seen at each tick, within one
    lane's own output, dropping any later row at a tick already seen.

    rows may be [tick, value] pairs or (tick, value, source) triples; only
    index 0 (the tick) is inspected. Order is preserved, so "first" means
    the order the rows were appended in (the lane's authored item order)."""
    seen_ticks: set[int] = set()
    result = []
    for row in rows:
        tick = row[0]
        if tick in seen_ticks:
            continue
        seen_ticks.add(tick)
        result.append(row)
    return result


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
    return notes_out, _dedup_same_tick(pitch_bends_out)


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
    tracks = [_serialize_track(t, denominator) for t in project.tracks]
    for track in tracks:
        pitch_bends = track.get('pitch-bends')
        if pitch_bends:
            # A slide spanning the full remaining bar produces its last
            # pitch-bend event exactly at loop_duration; the engine requires
            # tick < loop_duration, so pull that one event back by a tick.
            for pb in pitch_bends:
                if pb[0] == loop_duration:
                    pb[0] = loop_duration - 1
            pitch_bends.sort(key=lambda pb: pb[0])
    return {
        'header': {
            'bpm': project.bpm,
            'loop_duration': loop_duration,
        },
        'tracks': tracks,
    }
