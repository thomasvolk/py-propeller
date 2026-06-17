# 6 · Validation & Error Feedback — Technical Specification

## Overview

Epic 6 extends existing modules to surface clear, actionable `PropellerValidationError` messages at the earliest possible moment — operator application, object construction, and connection attempt. No new modules are introduced: changes touch `propeller/notes.py` (duration guard on `__mul__`), `propeller/composition.py` (`Track` name and note-value validation; `Project` time-signature validation), `propeller/transport.py` (enriched connection error message), and `propeller/__init__.py` (re-export of the error hierarchy).

**Confidence Level:** 92% — All questions resolved. Residual 8%: exact error message wording is an implementation-time detail; T-9 is conditional on Epic 5 being implemented, but the test itself is fully specified.

---

## Architecture Overview

Six of the thirteen ACs map to behaviour already delivered by earlier epics:

| AC | Already delivered by | Evidence |
|----|---------------------|---------|
| AC-1 | Epic 1 | `Note.__call__` validates velocity; test T-5 in `epic-1-spec.md` |
| AC-3 | Epic 3 | `Track.__post_init__` enforces channel ∈ [1, 16]; test T-3 in `epic-3-spec.md` |
| AC-4 | Epic 3 | `Track.__post_init__` enforces instrument ∈ [0, 127]; test T-4 in `epic-3-spec.md` |
| AC-9 (partial) | Epic 2 | `PropellerClient.send()` wraps `OSError` as `PropellerConnectionError` with socket path and `__cause__`; test T-10 in `epic-2-spec.md` |
| AC-12 | Epic 1 | `PropellerValidationError` subclasses `PropellerError` in `propeller/errors.py` |
| AC-13 | Epic 2 | `PropellerConnectionError` subclasses `PropellerError` in `propeller/errors.py` |

Epic 6 adds the missing pieces across four files:

**`propeller/notes.py`** — `Note.__mul__` and `Rest.__mul__` currently call `dataclasses.replace(self, duration=beats)` unconditionally. A pre-condition guard is added: if `beats` is not a positive number, `PropellerValidationError` is raised naming the `duration` field. Error messages from `__mul__` must not include position context (F-1).

**`propeller/composition.py`** — `Track.__post_init__` gains two new validation steps (inserted after the existing channel/instrument checks):

1. Name non-empty guard: if `self.name` is falsy, raise `PropellerValidationError` naming `name`.
2. Note-value validation: detects single-lane vs multi-lane form (same rule as Epic 3 I-4: `isinstance(notes[0], list)` when non-empty). For the flat form, iterates `self.notes` with a 1-based counter and checks `velocity ∈ [0, 127]` on each `Note` instance; raises `PropellerValidationError` with `f"position {i}"` on first failure. For the multi-lane form, iterates each inner list with a lane counter (1-based) and a position counter (1-based within the lane); raises with `f"lane {lane_i}, position {pos_i}"` on first failure. `Rest` instances are skipped in both forms (no velocity field).

`Project.__post_init__` gains one new validation step:

1. `time_signature` must be a two-element tuple whose elements are both positive integers; raise `PropellerValidationError` naming `time_signature` otherwise.

**`propeller/transport.py`** — The `PropellerConnectionError` message constructed in `PropellerClient.send()` is extended to include an actionable suggestion. The suggestion is added directly in `PropellerClient.send()` (Q-2 resolved — not in `errors.py` or `.play()`). The `__cause__` chain is preserved.

**`propeller/__init__.py`** — Adds:

```python
from propeller.errors import PropellerError, PropellerValidationError, PropellerConnectionError
```

This makes all three classes importable from the top-level `propeller` package (NF-2).

**Validation ordering (F-6, AC-10):** Since `Track.__post_init__` and `Project.__post_init__` fire at construction time — before `.play()` is ever called — the ordering guarantee is structural. No additional mechanism is needed.

---

## Components

### `propeller/notes.py` (modified)

`Note.__mul__` and `Rest.__mul__` gain a guard before the `dataclasses.replace` call:

```python
if not isinstance(beats, (int, float)) or beats <= 0:
    raise PropellerValidationError(
        f"duration must be a positive number, got {beats!r}"
    )
```

No position context is included in this message (F-1).

### `propeller/composition.py` (modified)

**`Track.__post_init__`** — two new checks appended after the existing channel/instrument guards:

- If `not self.name`: raise `PropellerValidationError("name must be a non-empty string")`
- For each `(i, note)` in `enumerate(self.notes, start=1)`: if `isinstance(note, Note)` and `not (0 <= note.velocity <= 127)`, raise `PropellerValidationError` whose message includes `f"position {i}"`. `Rest` instances are skipped (no velocity field).

**`Project.__post_init__`** — one new check appended after the existing bpm/bars guards:

- `self.time_signature` must be a `tuple` with exactly two elements, both of which satisfy `isinstance(x, int) and not isinstance(x, bool) and x > 0`; raise `PropellerValidationError` naming `time_signature` otherwise.

### `propeller/transport.py` (modified)

The `except OSError` branch in `PropellerClient.send()` (Epic 2 I-7) currently constructs:

```python
raise PropellerConnectionError(
    f"Cannot connect to {DEFAULT_SOCKET_PATH}: {e}"
) from e
```

Epic 6 extends this message in the same location (`PropellerClient.send()`) to append an actionable suggestion:

```python
raise PropellerConnectionError(
    f"Cannot connect to {DEFAULT_SOCKET_PATH}: {e}. "
    "Make sure the propeller-engine is running."
) from e
```

### `propeller/__init__.py` (modified)

Re-exports exception classes so callers can write `from propeller import PropellerError` without knowing the internal `propeller.errors` sub-module.

---

## Data Model

No new types are introduced. All exception classes already exist from Epics 1 and 2.

| Type | Fields | Notes |
|------|--------|-------|
| `PropellerError` | — | `propeller/errors.py` (Epic 1). Base library exception. |
| `PropellerValidationError` | — | `propeller/errors.py` (Epic 1). Subclass of `PropellerError`. Raised for all DSL/structural failures. |
| `PropellerConnectionError` | — | `propeller/errors.py` (Epic 2). Subclass of `PropellerError`. Raised for socket failures. Message gains actionable suggestion in Epic 6. |
| `Note` | `pitch: int`, `duration: float = 1.0`, `velocity: int = 100` | `@dataclass(frozen=True)` from Epic 1. `__mul__` gains duration guard in Epic 6. |
| `Rest` | `duration: float = 1.0` | `@dataclass(frozen=True)` from Epic 1. `__mul__` gains duration guard in Epic 6. No velocity field; skipped in Track note-value validation. |
| `Track` | `name: str`, `channel: int`, `instrument: int`, `notes: list[Note \| Rest] \| list[list[Note \| Rest]]` | `@dataclass(frozen=True)` from Epic 3. channel ∈ [1, 16]. `__post_init__` gains name validation and velocity-only note-value validation in Epic 6; validation traverses both flat and multi-lane forms. |
| `Project` | `bpm: float`, `time_signature: tuple[int, int]`, `bars: int`, `tracks: list[Track]` | `@dataclass(frozen=True)` from Epic 3. `__post_init__` gains `time_signature` validation in Epic 6. |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID | Task | Type | PRD ref | Depends on |
|----|------|------|---------|------------|
| T-1 | Test: `C4 * 0` raises `PropellerValidationError`; `C4 * -1` raises; message names `duration`; message contains no position/bar context; `C4 * 0.5` and `C4 * 2` succeed | test | F-1, F-2, AC-2 | — |
| T-2 | Test: `Z * 0` raises `PropellerValidationError`; `Z * -2` raises; `Z * 2` succeeds | test | F-1, F-2, AC-2 | — |
| I-1 | Add duration guard to `Note.__mul__` and `Rest.__mul__`: if `beats` is not a positive number raise `PropellerValidationError` naming `duration` | impl | F-1, F-2 | T-1, T-2 |
| T-3 | Test: `track(name="")` raises `PropellerValidationError` whose message names field `name`; `track(name="Piano")` succeeds | test | F-4, AC-5 | — |
| I-2 | Add `name` non-empty validation to `Track.__post_init__`: if `not self.name` raise `PropellerValidationError` naming `name` | impl | F-4 | T-3 |
| T-4 | Test (flat form): `Track(name="X", channel=1, instrument=0, notes=[Note(60, 1.0, 200)])` raises `PropellerValidationError` whose message contains "position 1"; constructing with `[C4, Note(60, 1.0, 200)]` raises with "position 2"; `Rest` at any position does not trigger the velocity check (AC-11) | test | F-9, AC-11 | I-2 |
| T-4b | Test (multi-lane form): `Track(name="X", channel=1, instrument=0, notes=[[C4()], [Note(60, 1.0, 200)]])` raises `PropellerValidationError` whose message contains "lane 2, position 1"; `Rest` in a lane does not trigger the check (AC-14) | test | F-9, AC-14 | I-2 |
| I-3 | Add note-value validation to `Track.__post_init__`: detect flat vs multi-lane form; for flat, iterate with 1-based index, check `velocity ∈ [0, 127]` per `Note`, raise with `f"position {i}"`; for multi-lane, iterate lanes and positions, raise with `f"lane {lane_i}, position {pos_i}"`; skip `Rest` in both forms | impl | F-9 | T-4, T-4b |
| T-5 | Test: `project(bpm=120, bars=2, time_signature=(4, 0), tracks=[])` raises `PropellerValidationError` naming `time_signature`; same for `(4,)`, `"4/4"`, `(0, 4)`, `(-1, 4)`, `(True, 4)`; `(4, 4)` and `(3, 8)` succeed | test | F-5, AC-8 | — |
| I-4 | Add `time_signature` validation to `Project.__post_init__`: must be a tuple of exactly two elements, both positive integers (exclude `bool`); raise `PropellerValidationError` naming `time_signature` | impl | F-5 | T-5 |
| T-6 | Test: via `mock.patch('socket.socket')` where `connect` raises `OSError`, verify `PropellerClient.send()` raises `PropellerConnectionError` whose message contains the socket path AND a phrase about verifying the engine is running; `.__cause__` is the original `OSError` | test | F-7, F-8, AC-9 | — |
| I-5 | Update the `except OSError` branch in `PropellerClient.send()` to append "Make sure the propeller-engine is running." to the `PropellerConnectionError` message | impl | F-7, F-8 | T-6 |
| T-7 | Test: `PropellerError`, `PropellerValidationError`, `PropellerConnectionError` are importable via `from propeller import …`; `isinstance(PropellerValidationError(), PropellerError)` is `True`; `isinstance(PropellerConnectionError(), PropellerError)` is `True`; `PropellerValidationError` is not a subclass of `PropellerConnectionError` | test | F-10, NF-2, AC-12, AC-13 | — |
| I-6 | Add `from propeller.errors import PropellerError, PropellerValidationError, PropellerConnectionError` to `propeller/__init__.py` | impl | F-10, NF-2 | T-7 |
| T-8 | Integration test: constructing `project(bpm=120, bars=2, time_signature=(4,4), tracks=[track(name="X", channel=17, instrument=0, notes=[])])` raises `PropellerValidationError`; a `socket.socket` mock is never called — confirming no socket is opened when validation fails | test | F-6, AC-10 | I-1, I-2, I-3, I-4, I-5, I-6 |
| T-9 | Integration test (requires Epic 5): calling `.play()` on a valid project when the engine is unreachable raises `PropellerConnectionError` whose message contains the socket path and the "engine is running" suggestion; `.__cause__` is an `OSError` | test | F-7, F-8, AC-9 | I-5, I-6 — Epic 5 must be implemented |

---

## Open Questions

None — all questions resolved.

---

## Open Decisions

None at this time.

---

## Revision Log

### Cycle 1 — Confidence: 72%
- Reconciled: nothing (spec created fresh from PRD)
- Added: Q-1 (note-value validation scope in Track), Q-2 (connection error suggestion placement)
- Note: six of thirteen ACs are already covered by Epics 1–3; T-9 blocked on Epic 5 implementation

### Cycle 2 — Confidence: 92%
- Reconciled: Q-1-A → note-value validation in `Track.__post_init__` checks velocity only; `Rest` instances skipped; architecture, components, I-3, T-4, and data model updated
- Reconciled: Q-2-A → suggestion added directly in `PropellerClient.send()`; architecture and components updated; I-5 and T-6 confirmed
- No open questions or decisions remain; specification is complete

### Cycle 3 — Confidence: 91%
- Context: briefing.md updated with multi-lane overlapping notes requirement.
- Components: `Track.__post_init__` note-value validation updated to detect flat vs multi-lane form; multi-lane path reports "lane N, position M" in error messages.
- Data Model: `Track.notes` type updated to `list[Note | Rest] | list[list[Note | Rest]]`.
- Tasks: T-4 narrowed to flat form; T-4b added for multi-lane velocity validation; I-3 updated to handle both forms.
