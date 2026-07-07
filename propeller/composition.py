import dataclasses

from propeller.errors import PropellerValidationError
from propeller.notes import Note, PitchBend, Rest


@dataclasses.dataclass(frozen=True)
class Track:
    name: str
    channel: int
    instrument: int
    notes: list

    def __post_init__(self) -> None:
        if not (1 <= self.channel <= 16):
            raise PropellerValidationError(
                f'channel {self.channel} is outside the valid range [1, 16]'
            )
        if not (0 <= self.instrument <= 127):
            raise PropellerValidationError(
                f'instrument {self.instrument} is outside the valid range [0, 127]'
            )
        if not self.name:
            raise PropellerValidationError('name must be a non-empty string')
        if self.notes and isinstance(self.notes[0], list):
            for lane_i, lane in enumerate(self.notes, start=1):
                self._validate_lane(lane, lane_i)
        else:
            self._validate_lane(self.notes)

    def _validate_lane(self, lane, lane_i=None) -> None:
        prev_was_pb = False
        for pos_i, note in enumerate(lane, start=1):
            if not isinstance(note, (Note, Rest, PitchBend)):
                loc = f'lane {lane_i}, position {pos_i}' if lane_i else f'notes[{pos_i}]'
                suffix = 'not a Note, Rest, or PitchBend instance' if lane_i else 'is not a Note or Rest instance'
                raise PropellerValidationError(f'{loc}: {suffix}')
            if isinstance(note, PitchBend):
                if prev_was_pb:
                    raise PropellerValidationError(
                        'consecutive pitch-bend elements are not permitted'
                    )
                prev_was_pb = True
            else:
                if isinstance(note, Note) and not (0 <= note.velocity <= 127):
                    if lane_i:
                        raise PropellerValidationError(
                            f'Invalid velocity at lane {lane_i}, position {pos_i}: '
                            f'value {note.velocity} exceeds valid range [0, 127]'
                        )
                    else:
                        raise PropellerValidationError(
                            f'Invalid velocity at position {pos_i}: value {note.velocity} '
                            f'exceeds valid range [0, 127]'
                        )
                prev_was_pb = False


@dataclasses.dataclass(frozen=True)
class Project:
    bpm: float
    time_signature: tuple
    bars: int
    tracks: list

    def __post_init__(self) -> None:
        if not self.bpm > 0:
            raise PropellerValidationError(
                f'bpm must be positive, got {self.bpm}'
            )
        if (
            not isinstance(self.bars, int)
            or isinstance(self.bars, bool)
            or self.bars <= 0
        ):
            raise PropellerValidationError(
                f'bars must be a positive integer, got {self.bars!r}'
            )
        ts = self.time_signature
        if (
            not isinstance(ts, tuple)
            or len(ts) != 2
            or not all(isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in ts)
        ):
            raise PropellerValidationError(
                f'time_signature must be a two-element tuple of positive integers, got {ts!r}'
            )

    def play(self) -> None:
        from propeller.player import play as _play
        _play(self)
