import dataclasses

from propeller.errors import PropellerValidationError

__all__: list[str] = []


@dataclasses.dataclass(frozen=True)
class PitchBend:
    value: float = 0.0

    def __post_init__(self) -> None:
        if not (-1.0 <= self.value <= 1.0):
            raise PropellerValidationError(
                f'pitch bend value {self.value} is outside the valid range [-1.0, 1.0]'
            )

    def __call__(self, value: float) -> 'PitchBend':
        return PitchBend(value)


PB = PitchBend()
__all__.append('PB')

_SEMITONES: list[tuple[str, ...]] = [
    ('C',),
    ('Cs', 'Df'),
    ('D',),
    ('Ds', 'Ef'),
    ('E',),
    ('F',),
    ('Fs', 'Gf'),
    ('G',),
    ('Gs', 'Af'),
    ('A',),
    ('As', 'Bf'),
    ('B',),
]


@dataclasses.dataclass(frozen=True)
class Note:
    pitch: int
    duration: float = 1.0
    velocity: int = 100

    def __mul__(self, beats: float) -> 'Note':
        if not isinstance(beats, (int, float)) or isinstance(beats, bool) or beats <= 0:
            raise PropellerValidationError(
                f"duration must be a positive number, got {beats!r}"
            )
        return dataclasses.replace(self, duration=beats)

    def __call__(self, velocity: int = 100) -> 'Note':
        if not (0 <= velocity <= 127):
            raise PropellerValidationError(
                f'velocity {velocity} is outside the valid range [0, 127]'
            )
        return dataclasses.replace(self, velocity=velocity)


@dataclasses.dataclass(frozen=True)
class Rest:
    duration: float = 1.0

    def __mul__(self, beats: float) -> 'Rest':
        if not isinstance(beats, (int, float)) or isinstance(beats, bool) or beats <= 0:
            raise PropellerValidationError(
                f"duration must be a positive number, got {beats!r}"
            )
        return dataclasses.replace(self, duration=beats)


@dataclasses.dataclass(frozen=True)
class _SlideInterval:
    """A single whole-tone (or partial, trailing) step within a Slide.

    Internal, musical-units-only representation (no ticks/PPQN knowledge).
    Not part of the public API.
    """
    start_pitch: int
    end_pitch: int
    tone_width: float


@dataclasses.dataclass(frozen=True)
class Slide:
    start: 'Note'
    end: 'Note'
    steps: float = 0.01
    duration: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.start, Note) or not isinstance(self.end, Note):
            raise PropellerValidationError(
                'start and end must be Note instances'
            )
        if (
            not isinstance(self.steps, (int, float))
            or isinstance(self.steps, bool)
            or not (0 < self.steps <= 1.0)
        ):
            raise PropellerValidationError(
                f'steps must be a positive number no greater than 1.0, got {self.steps!r}'
            )
        if self.start.pitch == self.end.pitch:
            raise PropellerValidationError(
                'start and end must have different pitches'
            )

    def __mul__(self, beats: float) -> 'Slide':
        if not isinstance(beats, (int, float)) or isinstance(beats, bool) or beats <= 0:
            raise PropellerValidationError(
                f"duration must be a positive number, got {beats!r}"
            )
        return dataclasses.replace(self, duration=beats)

    def intervals(self) -> list['_SlideInterval']:
        start_pitch = self.start.pitch
        end_pitch = self.end.pitch
        direction = 1 if end_pitch > start_pitch else -1
        remaining = abs(end_pitch - start_pitch)
        result: list['_SlideInterval'] = []
        current = start_pitch
        while remaining > 0:
            step = min(2, remaining)
            next_pitch = current + direction * step
            result.append(_SlideInterval(current, next_pitch, step / 2.0))
            current = next_pitch
            remaining -= step
        return result


for _octave in range(9):
    for _semitone, _names in enumerate(_SEMITONES):
        _pitch = (_octave + 1) * 12 + _semitone
        for _name in _names:
            _const_name = f'{_name}{_octave}'
            globals()[_const_name] = Note(_pitch)
            __all__.append(_const_name)

Z = Rest()
z = Rest()
__all__.extend(['Z', 'z'])
