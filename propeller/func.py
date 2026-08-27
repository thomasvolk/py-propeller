import random
from typing import Protocol, Union

from propeller.errors import PropellerValidationError
from propeller.notes import Note, Rest, Z

__all__ = ['probability', 'selection']

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


class _Selection:
    def __init__(self, value):
        self._value = value
        self._branches: list[tuple[bool, object]] = []
        self._default = None

    def _compare(self, threshold, *, before: bool) -> bool:
        try:
            return self._value < threshold if before else self._value >= threshold
        except TypeError as exc:
            raise PropellerValidationError(
                f'threshold must be comparable to the selection value, got {threshold!r}'
            ) from exc

    def before(self, threshold, value) -> '_Selection':
        self._branches.append((self._compare(threshold, before=True), value))
        return self

    def after(self, threshold, value) -> '_Selection':
        self._branches.append((self._compare(threshold, before=False), value))
        return self

    def default(self, value) -> '_Selection':
        self._default = value
        return self

    def select(self):
        result = self._default
        for matched, value in self._branches:
            if matched:
                result = value
        return result


def selection(value) -> _Selection:
    return _Selection(value)
