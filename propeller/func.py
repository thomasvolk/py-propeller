import random
from typing import Protocol, Union

from propeller.errors import PropellerValidationError
from propeller.notes import Note, Rest, Z

__all__ = ['probability']

NoteLike = Union[Note, Rest]


class Rng(Protocol):
    def random(self) -> float: ...


def _require_note(value: NoteLike, name: str) -> None:
    if not isinstance(value, (Note, Rest)):
        raise PropellerValidationError(
            f'{name} must be a Note or Rest, got {value!r}'
        )


def _require_probability(p: float) -> None:
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not (0.0 <= p <= 1.0):
        raise PropellerValidationError(
            f'probability must be a number in [0.0, 1.0], got {p!r}'
        )


def probability(p: float, note: NoteLike, *, replacement: NoteLike = Z, rng: Rng = random) -> NoteLike:
    _require_probability(p)
    _require_note(note, 'note')
    _require_note(replacement, 'replacement')
    return note if rng.random() < p else replacement
