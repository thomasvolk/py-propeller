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


from propeller.notes.Slide import Slide, SlideTarget, to  # noqa: E402

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
