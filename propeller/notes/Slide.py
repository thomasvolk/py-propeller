import dataclasses
import math
from typing import Callable

from propeller.errors import PropellerValidationError
from . import Note, PitchBend, Rest

__all__: list[str] = ['to', 'sin', 'cos', 'gauss']


def _validate_steps(steps: float) -> None:
    if (
        not isinstance(steps, (int, float))
        or isinstance(steps, bool)
        or not (0 < steps <= 1.0)
    ):
        raise PropellerValidationError(
            f'steps must be a positive number no greater than 1.0, got {steps!r}'
        )


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
        _validate_steps(self.steps)

    def value_at(self, progress: float) -> float:
        return self.value * progress


def to(value: float, steps: float = 0.01) -> SlideTarget:
    return SlideTarget(value, steps)


@dataclasses.dataclass(frozen=True)
class SlideCurve:
    """A slide's pitch-bend curve, evaluated as a function of progress (0.0
    at the slide's start to 1.0 at its end). Produced by sin()/cos()/gauss()
    or built directly for a custom shape."""
    func: Callable[[float], float]
    steps: float = 0.01

    def __post_init__(self) -> None:
        if not callable(self.func):
            raise PropellerValidationError('curve function must be callable')
        _validate_steps(self.steps)

    def value_at(self, progress: float) -> float:
        return self.func(progress)


def sin(amp: float = 2.0, period: float = 1.0, y_offset: float = 0.0, steps: float = 0.01) -> SlideCurve:
    return SlideCurve(lambda p: amp * math.sin(p * period * math.pi) + y_offset, steps)


def cos(amp: float = 2.0, period: float = 1.0, y_offset: float = 0.0, steps: float = 0.01) -> SlideCurve:
    return SlideCurve(lambda p: amp * math.cos(p * period * math.pi) + y_offset, steps)


def gauss(u: float = 0.0, o: float = 1.0, steps: float = 0.01) -> SlideCurve:
    """A normalized standard-normal PDF (peak scaled to 1.0), sampled across
    the fixed window [u - 3*o, u + 3*o] as progress runs 0.0 -> 1.0."""
    def _value(p: float) -> float:
        x = u - 3 * o + p * (6 * o)
        return math.exp(-0.5 * ((x - u) / o) ** 2)
    return SlideCurve(_value, steps)


@dataclasses.dataclass(frozen=True)
class Slide:
    start: Note
    target: SlideTarget | SlideCurve | Callable[[float], float]
    duration: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.start, Note):
            raise PropellerValidationError('start must be a Note instance')
        target_is_domain_item = isinstance(self.target, (Note, PitchBend, Rest))
        target_is_curve = isinstance(self.target, (SlideTarget, SlideCurve))
        if target_is_domain_item or not (target_is_curve or callable(self.target)):
            raise PropellerValidationError(
                "target must be produced by to(...)/sin(...)/cos(...)/gauss(...), "
                "or be a custom progress -> value function, e.g. Slide(C4, to(1.0))"
            )

    def __mul__(self, beats: float) -> 'Slide':
        if not isinstance(beats, (int, float)) or isinstance(beats, bool) or beats <= 0:
            raise PropellerValidationError(
                f"duration must be a positive number, got {beats!r}"
            )
        return dataclasses.replace(self, duration=beats)
