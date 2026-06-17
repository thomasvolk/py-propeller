# 4 · JSON Serialization — Technical Specification

## Overview

Epic 4 introduces `propeller/serializer.py`, a pure data-transformation module that converts a
project domain object into a Python dict matching the `create-project` wire format expected by
the transport layer (Epic 2). The serializer has no socket I/O, no file I/O, and no import
dependency on the transport or DSL layers. A minimal stub domain model (dataclasses) is defined
alongside the tests to enable parallel development while Epic 3 is in progress.

**Confidence Level:** 100% — All questions resolved; architecture, data model, and task table
fully cover every F-x and AC-x. Epic 1 integration confirmed: `propeller.notes.Rest` exposes
`duration: float`; serializer uses `item.duration`.

---

## Architecture Overview

A single new module is introduced:

- `propeller/serializer.py` — contains `PPQN = 480` (module-level constant), the public
  `serialize(project) -> dict` function, and private helpers `_serialize_track` and
  `_beats_to_ticks`. Has no imports from `propeller.transport` or any other transport module
  (F-13, F-14). Imports `Rest` from `propeller.notes` (Epic 1 note primitives).

A stub domain model for testing lives in `tests/stubs.py` (not shipped as part of the library).
It mirrors the field contract defined in F-15. `StubRest` inherits from `propeller.notes.Rest`,
ensuring `isinstance(item, Rest)` returns `True` inside the serializer.

**Serialization flow inside `serialize(project)`:**

Single-lane form (flat `track.notes`):
```python
from propeller.notes import Rest

for track in project.tracks:
    tick_cursor = 0
    notes_out   = []
    for item in track.notes:
        duration_ticks = _beats_to_ticks(item.duration)
        if isinstance(item, Rest):
            tick_cursor += duration_ticks
        else:
            notes_out.append([tick_cursor, duration_ticks, item.pitch, item.velocity])
            tick_cursor += duration_ticks
```

Multi-lane form (detected by `track.notes and isinstance(track.notes[0], list)`):
```python
all_notes = []
for lane in track.notes:           # each lane is independent
    for item in _serialize_lane(lane):
        all_notes.append(item)
notes_out = sorted(all_notes, key=lambda n: n[0])   # stable sort by start_tick (F-17)
```

`_serialize_lane(lane)` applies the same tick-cursor logic as the single-lane path and returns
a list of `[start_tick, duration_ticks, pitch, velocity]` entries.

---

## Components

### `propeller/serializer.py`

**`PPQN: int = 480`** — module-level constant; never re-read from config (F-10).

**`serialize(project) -> dict`** — public entry point (F-1). Returns a dict with exactly two
top-level keys `"header"` and `"tracks"`; never includes `"command"` (F-2). Delegates to
`_serialize_track` for each track.

**`_beats_to_ticks(beats: float) -> int`** — applies `round(beats * PPQN)` (F-10, F-12).

**`_serialize_lane(lane) -> list`** — iterates a single lane (a flat list of Note/Rest items),
accumulates `tick_cursor` from 0, and returns a list of `[start_tick, duration_ticks, pitch,
velocity]` entries. Rest items advance the cursor but produce no output entry (F-11).

**`_serialize_track(track) -> dict`** — detects single-lane vs multi-lane form. Single-lane:
delegates to `_serialize_lane` directly. Multi-lane: calls `_serialize_lane` for each inner
list, concatenates all results, and sorts by `start_tick` (stable, F-17). Returns
`{"name": …, "channel": …, "instrument": …, "notes": […]}` (F-7, F-8, F-9, F-11, F-16, F-17).

Imports: `from propeller.notes import Rest` — no import from `propeller.transport` (F-14).
The `Rest` import from the note primitives module is permitted; F-14 only excludes the
transport layer.

### `tests/stubs.py`

Provides `@dataclass` types that mirror the Epic 3 domain model contract (F-15).
`StubRest` inherits from `propeller.notes.Rest`, ensuring `isinstance(item, Rest)` returns
`True` in the serializer when given a `StubRest`.

- `StubProject` — fields: `bpm: int`, `time_signature: tuple[int, int]`, `bars: int`,
  `tracks: list`
- `StubTrack` — fields: `name: str`, `channel: int`, `instrument: int`, `notes: list`
- `StubNote` — fields: `duration: float`, `pitch: int`, `velocity: int`
- `StubRest(Rest)` — inherits from `propeller.notes.Rest`; field: `duration: float`;
  passes `isinstance(item, Rest)` check in the serializer

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `PPQN` | `int = 480` | Module-level constant in `propeller/serializer.py`. |
| `Rest` | `duration: float` (at minimum) | Defined in `propeller.notes` (Epic 1). Serializer imports via `from propeller.notes import Rest` and uses `isinstance`. |
| `StubProject` | `bpm: int`, `time_signature: tuple[int,int]`, `bars: int`, `tracks: list` | Test stub; mirrors Epic 3 domain model (F-15). |
| `StubTrack` | `name: str`, `channel: int`, `instrument: int`, `notes: list` | Test stub; `notes` is either a flat list of `StubNote`/`StubRest` objects (single-lane) or a list of such lists (multi-lane), mirroring the Epic 3 dual-form contract. DSL channel is 1-indexed; serializer passes it through unchanged. |
| `StubNote` | `duration: float`, `pitch: int`, `velocity: int` | Pitched note stub. `isinstance(item, Rest)` is `False`. |
| `StubRest` | `duration: float` (inherits `Rest`) | Rest stub; `isinstance(item, Rest)` is `True`. |
| Output dict (header) | `bpm: int`, `loop_duration: int` | `loop_duration = project.bars × time_signature[0] × 480` (F-5). |
| Output dict (track) | `name: str`, `channel: int`, `instrument: int`, `notes: list[list[int]]` | Each note entry is `[start_tick, duration_ticks, pitch, velocity]` (F-7, F-8). `channel` is 1-indexed (1–16), passed through directly from the DSL value. |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID   | Task | Type | PRD ref | Depends on |
|------|------|------|---------|------------|
| T-1  | Test: `StubProject`, `StubTrack`, `StubNote`, `StubRest` instantiate with expected fields; `isinstance(StubRest(...), Rest)` is `True`; `isinstance(StubNote(...), Rest)` is `False` | test | F-15 | — |
| I-1  | Create `tests/stubs.py` with `StubProject`, `StubTrack`, `StubNote`, and `StubRest(Rest)` per F-15 contract; `StubRest` inherits from the domain `Rest` class | impl | F-15 | T-1 |
| T-2  | Test: `serialize(project)` returns a `dict` with keys `"header"` and `"tracks"` and no `"command"` key | test | AC-1, F-1, F-2 | I-1 |
| I-2  | Create `propeller/serializer.py`; implement `serialize()` skeleton returning `{"header": {}, "tracks": []}` with no `"command"` key; import `Rest` from domain model; no imports from transport (F-13, F-14) | impl | F-1, F-2, F-13, F-14 | T-2 |
| T-3  | Test: `result["header"]["bpm"]` equals `project.bpm` for arbitrary BPM values | test | AC-2, F-3, F-4 | I-2 |
| I-3  | Populate `header["bpm"]` from `project.bpm` | impl | F-3, F-4 | T-3 |
| T-4  | Test: `result["header"]["loop_duration"]` equals `bars × time_signature[0] × 480`; verify with `bars=1, ts=(4,4) → 1920` (AC-3) and `bars=3, ts=(4,4) → 5760` (AC-9) | test | AC-3, AC-9, F-5 | I-3 |
| I-4  | Compute and populate `header["loop_duration"] = project.bars * project.time_signature[0] * PPQN` | impl | F-5 | T-4 |
| T-5  | Test: `result["tracks"]` has one entry per track; each entry has keys `"name"`, `"channel"`, `"instrument"`, `"notes"`; values match track fields (AC-6, F-6, F-7) | test | AC-6, F-6, F-7 | I-4 |
| I-5  | Implement `_serialize_track(track)` returning `{"name": …, "channel": …, "instrument": …, "notes": []}` and build `result["tracks"]` via list comprehension | impl | F-6, F-7 | T-5 |
| T-6  | Test: a single `StubNote(duration=2, pitch=60, velocity=80)` maps to `[0, 960, 60, 80]` (AC-7, F-8) | test | AC-7, F-8, F-10 | I-5 |
| T-7  | Test: two consecutive quarter-note `StubNote` objects give `start_tick` 0 and 480 respectively (AC-4, F-9) | test | AC-4, F-9 | I-5 |
| I-6  | Implement tick accumulation in `_serialize_track`: `start_tick` is cumulative sum of preceding durations; call `_beats_to_ticks`; append `[start_tick, duration_ticks, pitch, velocity]` per pitched note | impl | F-8, F-9, F-10 | T-6, T-7 |
| T-8  | Test: a `StubRest(duration=1)` followed by a `StubNote` quarter note yields exactly one entry in `notes` with `start_tick == 480` (AC-5, F-11) | test | AC-5, F-11 | I-6 |
| I-7  | Add rest branch in `_serialize_track`: `if isinstance(item, Rest)`, advance `tick_cursor` but do not append to `notes_out` | impl | F-11 | T-8 |
| T-9  | Test: `StubNote(duration=1/3)` yields `duration_ticks == round(1/3 * 480) == 160`; no exception raised (AC-10, F-12) | test | AC-10, F-12 | I-7 |
| I-8  | Implement `_beats_to_ticks(beats: float) -> int` using `round(beats * PPQN)`; use it in all tick computations | impl | F-10, F-12 | T-9 |
| T-10 | Test: `import propeller.serializer` succeeds in a subprocess with no socket, no engine running; module is callable (AC-8, F-13, F-14, NF-2, NF-3) | test | AC-8, F-13, F-14, NF-2, NF-3 | I-2 |
| T-11 | Test: three single-note lanes `[[C4(80)], [E4(80)], [G4(80)]]` serialize to exactly 3 entries all with `start_tick=0` and correct pitches/velocities (AC-11, F-16, F-17) | test | AC-11, F-16, F-17 | I-7 |
| T-12 | Test: two-lane track `[[C4(), D4()], [E4()]]` serializes to 3 entries: C4 at tick 0, E4 at tick 0, D4 at tick 480 (sorted by start_tick, stable within tie) (AC-12, F-9, F-16, F-17) | test | AC-12, F-9, F-16, F-17 | I-7 |
| I-9  | Extract `_serialize_lane(lane)` from the single-lane path in `_serialize_track`; add multi-lane detection (`isinstance(track.notes[0], list)` when non-empty); call `_serialize_lane` per inner list, concatenate, and sort by `start_tick` | impl | F-16, F-17 | T-11, T-12 |

---

## Open Questions

None — all questions resolved.

---

## Open Decisions

None.

---

## Revision Log

### Cycle 1 — Confidence: 78%
- Reconciled: nothing (spec created fresh from PRD)
- Added: Q-1 (rest detection mechanism — pitch sentinel vs type check vs property)

### Cycle 2 — Confidence: 78%
- Reconciled: nothing (Q-1 unanswered)
- Added: nothing (Q-1 covers the only remaining ambiguity)

### Cycle 3 — Confidence: 83%
- Reconciled: Q-1 → B (isinstance check); Architecture Overview pseudocode updated, Components updated (Rest import noted), Data Model updated (Rest row added, StubRest now inherits Rest), I-1 and I-7 updated, T-1 updated
- Added: Q-2 (which module exports the Rest class the serializer imports)

### Cycle 4 — Confidence: 92%
- Reconciled: Q-2 → A (`propeller.notes`); Architecture Overview, Components, and Data Model updated with concrete `from propeller.notes import Rest`; StubRest now explicitly inherits from `propeller.notes.Rest`
- Added: nothing (no open questions or decisions remain)

### Cycle 5 — Confidence: 92%
- Context: briefing.md updated with multi-lane overlapping notes requirement.
- Architecture Overview: multi-lane serialization flow added alongside single-lane flow.
- Components: `_serialize_lane` extracted as a named helper; `_serialize_track` updated to detect lane form and sort merged results by start_tick.
- Data Model: `StubTrack.notes` updated to support both flat and list-of-lists forms.
- Tasks: T-11, T-12 (multi-lane tests) and I-9 (lane detection + merge impl) added.
