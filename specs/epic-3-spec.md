# 3 · Composition Model — Technical Specification

## Overview

Epic 3 introduces `Track` and `Project` as frozen dataclasses in `propeller/composition.py`.
`Track` groups a flat ordered list of `Note`/`Rest` instances (from Epic 1) under a named MIDI
voice; `Project` binds one or more tracks with global playback parameters (BPM, time signature,
bar count). Both types are exposed as lowercase DSL callables (`track`, `project`) via
`propeller/__init__.py`. All validation fires in `__post_init__`, reusing `PropellerValidationError`
from Epic 1.

**Confidence Level:** 93% — All decisions resolved; architecture, data model, and task table are
fully concrete. Residual 7%: exact error message wording for validation failures is an
implementation-time detail, and `bpm` type coercion (int vs float) is not formally specified.

---

## Architecture Overview

Three files are involved:

- `propeller/errors.py` — **unchanged from Epic 1**; `PropellerError` and
  `PropellerValidationError` already defined there.
- `propeller/composition.py` — new file; defines `Track` and `Project` frozen dataclasses with
  `__post_init__` validation. No I/O, no external dependencies.
- `propeller/__init__.py` — updated to expose `track = Track` and `project = Project` as the
  public DSL callables (F-6). Currently an empty package marker from Epic 1.

**Construction and validation flow:**

```
track(name="Piano", channel=2, instrument=0, notes=[C4, D4])   # flat / single-lane
track(name="Piano", channel=2, instrument=0, notes=[[C4], [E4]])  # multi-lane
    └─ Track.__post_init__
           ├─ channel ∈ [1, 16]          → PropellerValidationError if violated (F-9)
           ├─ instrument ∈ [0, 127]      → PropellerValidationError if violated (F-9)
           ├─ detect form: notes and isinstance(notes[0], list) → multi-lane; else single-lane (F-14)
           ├─ single-lane: for i, n in enumerate(notes, 1):
           │      isinstance(n, (Note, Rest)) → PropellerValidationError(pos=i) if not (F-12)
           └─ multi-lane: for lane_i, lane in enumerate(notes, 1):
                  for pos_i, n in enumerate(lane, 1):
                      isinstance(n, (Note, Rest)) → PropellerValidationError(lane=lane_i, pos=pos_i) if not (F-12, F-15)

project(bpm=120, time_signature=(4,4), bars=2, tracks=[t])
    └─ Project.__post_init__
           ├─ bpm > 0                    → PropellerValidationError if violated (F-10)
           └─ isinstance(bars, int) and bars > 0 → PropellerValidationError if violated (F-10)
```

`Note` and `Rest` are imported from `propeller.notes` inside `propeller/composition.py` for use
in the notes type check.

---

## Components

### `propeller/composition.py`

Owns the full domain model. Imports `Note`, `Rest` from `propeller.notes` and
`PropellerValidationError` from `propeller.errors`.

**`Track`** — `@dataclass(frozen=True)` with fields `name`, `channel`, `instrument`, `notes`.
`__post_init__` validates channel range, instrument range, and iterates `notes` for type
correctness (type-only check per Q8-A decision: Epic 1 owns note value correctness; track
owns structural correctness). The `notes` field accepts both the flat single-lane form and
the multi-lane list-of-lists form; the form is stored as-is and detected in `__post_init__`
by checking `isinstance(notes[0], list)` (empty `notes` defaults to single-lane).

**`Project`** — `@dataclass(frozen=True)` with fields `bpm`, `time_signature`, `bars`, `tracks`.
`__post_init__` validates `bpm > 0` and `isinstance(bars, int) and not isinstance(bars, bool) and bars > 0`.
Empty `tracks=[]` is always valid.

### `propeller/__init__.py`

Adds two module-level aliases after Epic 1 left this file empty:

```python
from propeller.composition import Track, Project

track = Track
project = Project
```

This keeps the DSL surface lowercase (`track(...)`, `project(...)`) while class names follow
Python conventions (`Track`, `Project`).

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `Track` | `name: str`, `channel: int`, `instrument: int`, `notes: list[Note \| Rest] \| list[list[Note \| Rest]]` | `@dataclass(frozen=True)`; validated in `__post_init__`; channel ∈ [1, 16], instrument ∈ [0, 127]; flat list → single lane; list of lists → multi-lane; detected via `isinstance(notes[0], list)` |
| `Project` | `bpm: float`, `time_signature: tuple[int, int]`, `bars: int`, `tracks: list[Track]` | `@dataclass(frozen=True)`; validated in `__post_init__`; bpm > 0, bars must be positive int |
| `PropellerError` | — | Defined in Epic 1 (`propeller/errors.py`); base library exception |
| `PropellerValidationError` | — | Defined in Epic 1 (`propeller/errors.py`); raised for all construction validation failures |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID   | Task | Type | PRD ref | Depends on |
|------|------|------|---------|------------|
| T-1  | Test `Track` construction: `Track(name="Piano", channel=2, instrument=0, notes=[C4, D4, E4, F4])` has `.name == "Piano"`, `.channel == 2`, `.instrument == 0`, `.notes` has length 4; `repr(t)` is a non-empty string | test | F-1, F-3, NF-2, AC-1, AC-3, AC-4 | — |
| T-2  | Test `Track(notes=[])` constructs without error; `.notes` is an empty list; `Track(notes=[C4])` allows `.notes[0]` access | test | F-5, F-13, AC-11 | — |
| T-3  | Test channel validation: `Track(channel=17, ...)` raises `PropellerValidationError`; `Track(channel=-1, ...)` raises; `Track(channel=0, ...)` raises; `Track(channel=1, ...)` and `Track(channel=16, ...)` succeed; raised error is instance of `PropellerError` with non-empty message | test | F-8, F-9, F-11, AC-6, AC-10 | — |
| T-4  | Test instrument validation: `Track(instrument=128, ...)` raises `PropellerValidationError`; `Track(instrument=-1, ...)` raises; `Track(instrument=0, ...)` and `Track(instrument=127, ...)` succeed | test | F-9, AC-7 | — |
| T-5  | Test notes type validation: `Track(notes=[C4, "bad", D4])` raises `PropellerValidationError` whose message contains the 1-based position (2); non-Note/Rest at first position also caught | test | F-12 | — |
| T-6  | Test `Track` immutability: `t.name = "Other"` raises `FrozenInstanceError` | test | F-7, NF-3, AC-13 | — |
| I-1  | Implement `Track` in `propeller/composition.py` as `@dataclass(frozen=True)` with `__post_init__` enforcing channel ∈ [1, 16], instrument ∈ [0, 127], and type-only notes iteration | impl | F-1, F-3, F-5, F-7, F-8, F-9, F-12, F-13 | T-1, T-2, T-3, T-4, T-5, T-6 |
| T-7  | Test `Project` construction: `Project(bpm=120, time_signature=(4,4), bars=2, tracks=[t])` has correct attributes; `repr(p)` is non-empty; `p.tracks[0].name` accessible without error | test | F-2, F-4, NF-2, AC-2, AC-3, AC-4 | I-1 |
| T-8  | Test `Project(tracks=[])` constructs without error; `.tracks` is an empty list | test | F-13, AC-12 | — |
| T-9  | Test bpm validation: `Project(bpm=0, ...)` raises `PropellerValidationError`; `Project(bpm=-1, ...)` raises; `Project(bpm=120, ...)` succeeds | test | F-10, AC-8 | — |
| T-10 | Test bars validation: `Project(bars=0, ...)` raises `PropellerValidationError`; `Project(bars=-1, ...)` raises; `Project(bars=1, ...)` succeeds; `Project(bars=2, ...)` succeeds | test | F-10, AC-9 | — |
| T-11 | Test `Project` immutability: `p.bpm = 200` raises `FrozenInstanceError` | test | F-7, NF-3, AC-14 | — |
| I-2  | Implement `Project` in `propeller/composition.py` as `@dataclass(frozen=True)` with `__post_init__` enforcing bpm > 0 and bars is positive int (not bool) | impl | F-2, F-4, F-7, F-10, F-13 | T-7, T-8, T-9, T-10, T-11 |
| T-12 | Test `from propeller import project, track`; both are callable; constructing a project with tracks works end-to-end | test | F-6, AC-5 | I-1, I-2 |
| I-3  | Add `from propeller.composition import Track, Project` and `track = Track; project = Project` to `propeller/__init__.py` | impl | F-6 | T-12 |
| T-13 | Test multi-lane construction: `Track(name="Piano", channel=1, instrument=0, notes=[[C4()], [E4()], [G4()]])` has `.notes` with length 3 and each inner list has length 1 (AC-15); `Track(notes=[[C4()], []])` succeeds and the empty inner lane is preserved (AC-16) | test | F-1, F-14, F-15, AC-15, AC-16 | I-1 |
| T-14 | Test multi-lane type validation: `Track(notes=[[C4(), "bad"]])` raises `PropellerValidationError` whose message contains "lane 1" and "position 2"; `Track(notes=[["bad"]])` raises with "lane 1, position 1" (AC-17) | test | F-12, F-14, AC-17 | I-1 |
| I-4  | Update `Track.__post_init__` to detect the multi-lane form (`isinstance(notes[0], list)` when `notes` is non-empty) and apply type validation per lane with lane+position error context; single-lane path unchanged | impl | F-12, F-14, F-15 | T-13, T-14 |

---

## Open Questions

None at this time.

---

## Open Decisions

None at this time.

---

## Revision Log

### Cycle 1 — Confidence: 78%
- Reconciled: Q8-A from PRD (type-only notes check) applied directly to I-1 and T-5 during initial spec creation
- Added: D-1 (collection field type: list vs tuple), D-2 (DSL alias strategy)

### Cycle 2 — Confidence: 93%
- Reconciled: D-1-A → `notes` and `tracks` stored as `list`; immutability is shallow (frozen=True prevents reassignment, not list mutation); data model and architecture already reflected this
- Reconciled: D-2-A → `Track`/`Project` as PascalCase class names; `track = Track`, `project = Project` aliases in `__init__.py`; architecture already reflected this
- Added: none — specification is complete at 93%

### Cycle 3 — Confidence: 92%
- Context: briefing.md updated with multi-lane overlapping notes requirement.
- Architecture Overview: validation flow updated to show both single-lane and multi-lane paths in `Track.__post_init__`.
- Components: `Track` description updated; `notes` field stores both forms as-is; form detected via `isinstance(notes[0], list)`.
- Data Model: `notes` type updated to `list[Note | Rest] | list[list[Note | Rest]]`.
- Tasks: T-13 (multi-lane construction), T-14 (multi-lane type validation), I-4 (detection + validation impl) added.
