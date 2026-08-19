import dataclasses

from propeller.errors import PropellerValidationError
from . import Note

__all__: list[str] = ['to']


@dataclasses.dataclass(frozen=True)
class SlideTarget:
    value: float
    steps: float = 0.01

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, (int, float))
            or isinstance(self.value, bool)
            or not (-1.0 <= self.value <= 1.0)
        ):
            raise PropellerValidationError(
                f'pitch bend target value {self.value} is outside the valid range [-1.0, 1.0]'
            )
        if self.value == 0.0:
            raise PropellerValidationError(
                'pitch bend target value must not be 0.0 (a Slide must actually move the pitch)'
            )
        if (
            not isinstance(self.steps, (int, float))
            or isinstance(self.steps, bool)
            or not (0 < self.steps <= 1.0)
        ):
            raise PropellerValidationError(
                f'steps must be a positive number no greater than 1.0, got {self.steps!r}'
            )


def to(value: float, steps: float = 0.01) -> SlideTarget:
    return SlideTarget(value, steps)


@dataclasses.dataclass(frozen=True)
class Slide:
    start: Note
    target: SlideTarget
    duration: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.start, Note):
            raise PropellerValidationError('start must be a Note instance')
        if not isinstance(self.target, SlideTarget):
            raise PropellerValidationError(
                "target must be produced by to(...), e.g. Slide(C4, to(1.0))"
            )

    def __mul__(self, beats: float) -> 'Slide':
        if not isinstance(beats, (int, float)) or isinstance(beats, bool) or beats <= 0:
            raise PropellerValidationError(
                f"duration must be a positive number, got {beats!r}"
            )
        return dataclasses.replace(self, duration=beats)
