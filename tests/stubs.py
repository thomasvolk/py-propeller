"""Stub domain model for Epic 4 serializer tests (mirrors Epic 3 contract)."""
import dataclasses

from propeller.notes import Rest


@dataclasses.dataclass(frozen=True)
class StubProject:
    bpm: int
    time_signature: tuple
    bars: int
    tracks: list


@dataclasses.dataclass(frozen=True)
class StubTrack:
    name: str
    channel: int
    instrument: int
    notes: list


@dataclasses.dataclass(frozen=True)
class StubNote:
    duration: float
    pitch: int
    velocity: int


@dataclasses.dataclass(frozen=True)
class StubRest(Rest):
    duration: float = 1.0
