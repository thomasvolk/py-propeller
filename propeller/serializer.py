from propeller.errors import PropellerValidationError
from propeller.notes import PitchBend, Rest

PPQN: int = 480


def _beats_to_ticks(beats: float, denominator: int = 4) -> int:
    return round(beats * PPQN * 4 / denominator)


def _pb_to_int(value: float) -> int:
    return int(round((value + 1.0) / 2.0 * 16383))


def _serialize_lane(lane, denominator: int = 4, emit_trailing_pb: bool = False) -> tuple[list, list]:
    tick_cursor = 0
    notes_out = []
    pitch_bends_out = []
    pending_pb_value: float | None = None
    pending_pb_tick: int = 0
    for item in lane:
        if isinstance(item, PitchBend):
            if pending_pb_value is not None:
                pitch_bends_out.append([pending_pb_tick, _pb_to_int(pending_pb_value)])
            pending_pb_value = item.value
            pending_pb_tick = tick_cursor
            continue
        duration_ticks = _beats_to_ticks(item.duration, denominator)
        if isinstance(item, Rest):
            tick_cursor += duration_ticks
        else:
            if pending_pb_value is not None:
                pitch_bends_out.append([pending_pb_tick, _pb_to_int(pending_pb_value)])
                pending_pb_value = None
            notes_out.append([tick_cursor, duration_ticks, item.pitch, item.velocity])
            tick_cursor += duration_ticks
    if emit_trailing_pb and pending_pb_value is not None:
        pitch_bends_out.append([pending_pb_tick, _pb_to_int(pending_pb_value)])
    return notes_out, pitch_bends_out


def _serialize_track(track, denominator: int = 4) -> dict:
    notes = track.notes
    if notes and isinstance(notes[0], list):
        all_notes = []
        all_pitch_bends = []
        for lane in notes:
            lane_notes, lane_pbs = _serialize_lane(lane, denominator, emit_trailing_pb=True)
            all_notes.extend(lane_notes)
            all_pitch_bends.extend(lane_pbs)
        ticks = [pb[0] for pb in all_pitch_bends]
        if len(ticks) != len(set(ticks)):
            raise PropellerValidationError(
                'multiple lanes produce a pitch bend at the same tick offset'
            )
        notes_out = sorted(all_notes, key=lambda n: n[0])
        pitch_bends_out = sorted(all_pitch_bends, key=lambda pb: pb[0])
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
