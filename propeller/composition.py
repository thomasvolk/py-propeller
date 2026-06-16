import dataclasses

from propeller.errors import PropellerValidationError
from propeller.notes import Note, Rest


@dataclasses.dataclass(frozen=True)
class Track:
    name: str
    channel: int
    instrument: int
    notes: list

    def __post_init__(self) -> None:
        if not (0 <= self.channel <= 15):
            raise PropellerValidationError(
                f'channel {self.channel} is outside the valid range [0, 15]'
            )
        if not (0 <= self.instrument <= 127):
            raise PropellerValidationError(
                f'instrument {self.instrument} is outside the valid range [0, 127]'
            )
        if not self.name:
            raise PropellerValidationError('name must be a non-empty string')
        for i, note in enumerate(self.notes, start=1):
            if not isinstance(note, (Note, Rest)):
                raise PropellerValidationError(
                    f'notes[{i}] is not a Note or Rest instance'
                )
            if isinstance(note, Note) and not (0 <= note.velocity <= 127):
                raise PropellerValidationError(
                    f'Invalid velocity at position {i}: value {note.velocity} '
                    f'exceeds valid range [0, 127]'
                )


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
