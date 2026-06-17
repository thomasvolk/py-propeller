from propeller.notes import Rest

PPQN: int = 480


def _beats_to_ticks(beats: float) -> int:
    return round(beats * PPQN)


def _serialize_track(track) -> dict:
    tick_cursor = 0
    notes_out = []
    for item in track.notes:
        duration_ticks = _beats_to_ticks(item.duration)
        if isinstance(item, Rest):
            tick_cursor += duration_ticks
        else:
            notes_out.append([tick_cursor, duration_ticks, item.pitch, item.velocity])
            tick_cursor += duration_ticks
    return {
        'name': track.name,
        'channel': track.channel,
        'instrument': track.instrument,
        'notes': notes_out,
    }


def serialize(project) -> dict:
    beats_per_bar = project.time_signature[0]
    loop_duration = project.bars * beats_per_bar * PPQN
    return {
        'header': {
            'bpm': project.bpm,
            'loop_duration': loop_duration,
        },
        'tracks': [_serialize_track(t) for t in project.tracks],
    }
