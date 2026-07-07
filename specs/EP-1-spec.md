# EP-1 · Pitch Bend DSL Element — Technical Specification

## Overview

This epic adds a `PB` pitch-bend DSL element to propeller. A composer writes `PB(value)` or bare `PB` in a track's note list to declare a pitch-bend event. The implementation touches three existing modules: `notes.py` (new `PitchBend` class and `PB` constant), `composition.py` (extended `Track` validation), and `serializer.py` (new `pitch_bends` output in serialized tracks).

**Confidence Level:** 93% — all questions resolved; minor residual ambiguity around the exact wording required in the consecutive-PB error message (the PRD says "identifying the consecutive pitch-bend elements" but does not prescribe the exact string).

---

## Architecture Overview

Three modules are modified; no new files are introduced.

**`propeller/notes.py`** gains a `PitchBend` frozen dataclass and a `PB` module-level constant. `PitchBend` follows the same pattern as `Note`: it is a frozen dataclass, validates its own fields in `__post_init__`, and is callable — `PB(0.5)` calls `PitchBend.__call__` and returns a new `PitchBend(0.5)`. `PB = PitchBend()` is the bare sentinel at `value=0.0`. Only `PB` is added to `__all__`; the class `PitchBend` is not exported (matching the convention for `Note` and `Rest`).

**`propeller/composition.py`** extends `Track.__post_init__` to accept `PitchBend` instances alongside `Note` and `Rest` in the notes list. It adds a consecutive-PB check: if two `PitchBend` elements appear adjacent **anywhere** in the sequence — whether before a note or at the trailing end — a `PropellerValidationError` is raised. In multi-lane mode the check is applied independently to each lane.

**`propeller/serializer.py`** extends `_serialize_lane` to track a pending `PitchBend` as the cursor advances. When a `PitchBend` is encountered, it is held in a buffer with no tick advance. When the next `Note` (or end-of-lane) is reached, the pending PB is emitted to a `pitch_bends` accumulator at the current tick cursor. `_serialize_lane` now returns `(notes_out, pitch_bends_out)`. `_serialize_track` collects per-lane pitch bend entries and adds a `pitch_bends` key to the track dict **only when the list is non-empty**; tracks with no `PB` elements receive no `pitch_bends` key, preserving backward compatibility with existing serialized output.

`PropellerValidationError` (already defined in `errors.py`) is used for all pitch-bend validation failures; no new exception type is needed because `PropellerValidationError` is already a DSL-specific type (not `ValueError` or `TypeError`).

---

## Components

### `PitchBend` dataclass (`propeller/notes.py`)

Frozen dataclass with a single field `value: float = 0.0`. `__post_init__` raises `PropellerValidationError` if `value` is outside `[-1.0, 1.0]`; the error message must include the invalid value and the accepted range. A `__call__(self, value: float) -> PitchBend` method returns a new `PitchBend(value)`, enabling the `PB(0.5)` DSL syntax.

### `PB` constant (`propeller/notes.py`)

Module-level singleton `PB = PitchBend()`. Added to `__all__`. When used bare it is already a `PitchBend(0.0)`; when called it delegates to `PitchBend.__call__`.

### `Track` validation (`propeller/composition.py`)

`__post_init__` is extended to:
- Allow `PitchBend` as a valid element in `notes` (single-lane and per-lane in multi-lane mode).
- Detect any two consecutive `PitchBend` elements — regardless of whether a note follows — and raise `PropellerValidationError`. The check runs on the flat note list for single-lane tracks and independently on each inner list for multi-lane tracks.

The existing element-type check (`not isinstance(note, (Note, Rest))`) gains `PitchBend` in the allowed set.

### Serializer lane processor (`propeller/serializer.py`)

`_serialize_lane` gains a `pitch_bend_buffer` (a pending `PitchBend | None`). When a `PitchBend` is encountered the buffer is set (no tick advance). When a `Note` is next, the buffered PB is flushed as `[tick_cursor, pb.value]`; the buffer is then cleared. At end-of-lane, any remaining buffered PB is flushed at the current `tick_cursor`. `_serialize_lane` now returns `(notes_out, pitch_bends_out)`.

`_serialize_track` collects pitch bends across lanes. If the combined `pitch_bends_out` is non-empty, it adds a `pitch_bends` key to the track dict. If it is empty the key is omitted entirely, so existing serialized output for PB-free tracks is unchanged.

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `PitchBend` | `value: float = 0.0` | Frozen dataclass; `__post_init__` validates `[-1.0, 1.0]`; `__call__(value)` creates a new `PitchBend` |
| `PB` | — | Singleton `PitchBend()` at module level; only DSL-visible form; in `notes.__all__` |
| serialized pitch bend entry | `[tick: int, value: float]` | Appended to `pitch_bends` list in serialized track dict; key is omitted when list would be empty |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID   | Task | Type | PRD ref | Depends on |
|------|------|------|---------|------------|
| T-1  | `PitchBend(0.5)` constructs with `value == 0.5` | test | F-1 | — |
| T-2  | `PitchBend(1.0)` and `PitchBend(-1.0)` are valid (boundary) | test | F-1 | — |
| T-3  | `PitchBend(1.5)` raises `PropellerValidationError` whose message contains `1.5` and `-1.0` and `1.0` | test | F-5, NF-1 | — |
| T-4  | `PitchBend(-1.5)` raises `PropellerValidationError` | test | F-5 | — |
| T-5  | Raised exception is `PropellerValidationError`, not `ValueError` or `TypeError` | test | NF-2, AC-7 | — |
| I-1  | Implement `PitchBend` frozen dataclass in `notes.py` with `__post_init__` validation | impl | F-1, F-5, NF-1, NF-2 | T-1–T-5 |
| T-6  | `PB` is an instance of `PitchBend` with `value == 0.0` | test | F-2 | I-1 |
| T-7  | `PB(0.5)` returns a `PitchBend` with `value == 0.5` and is not `PB` itself | test | F-2, AC-2 | I-1 |
| T-8  | `PB` is in `notes.__all__`; `PitchBend` is not in `notes.__all__` | test | F-2 | I-1 |
| I-2  | Add `__call__` to `PitchBend`; define `PB = PitchBend()`; add `PB` to `__all__` | impl | F-2 | T-6–T-8 |
| T-9  | `Track` accepts `[PB(0.5), C4]` without error | test | F-4, AC-1 | I-2 |
| T-10 | `Track` accepts trailing `[C4, PB(0.3)]` (single trailing PB, no following note) without error | test | F-6, AC-4 | I-2 |
| T-11 | `Track` with `[PB(0.5), PB(-0.3), D4]` raises `PropellerValidationError` | test | F-7, AC-5 | I-2 |
| T-12 | Raised exception for consecutive PBs before a note is `PropellerValidationError`, not `ValueError` | test | NF-2, AC-8 | I-2 |
| T-13 | `Track` with no `PB` elements constructs identically to current behaviour | test | F-8, AC-6 | I-2 |
| T-14 | `Track` with `[C4, PB(0.5), PB(-0.3)]` (trailing consecutive PBs) raises `PropellerValidationError` | test | F-7 | I-2 |
| T-15 | Multi-lane `Track` with `PB(0.5)` in lane 1 and `PB(-0.3)` in lane 2 (non-consecutive per-lane) is accepted | test | F-4 | I-2 |
| T-16 | Multi-lane `Track` with `[PB(0.5), PB(-0.3), C4]` in one lane raises `PropellerValidationError` | test | F-7 | I-2 |
| I-3  | Extend `Track.__post_init__` to allow `PitchBend` and detect any adjacent PBs (single-lane and per-lane) | impl | F-4, F-6, F-7, F-8 | T-9–T-16 |
| T-17 | `_serialize_lane([PB(0.5), note])` emits pitch bend at same tick as note; tick cursor not advanced by PB | test | F-3, F-4 | I-3 |
| T-18 | Serialized track dict has `pitch_bends` key containing `[tick, 0.5]` for `[PB(0.5), note]` | test | F-4 | I-3 |
| T-19 | Trailing `PB` at end of lane emits pitch bend entry at current cursor tick | test | F-6 | I-3 |
| T-20 | Serialized track with no `PB` elements has no `pitch_bends` key in the output dict | test | F-8, AC-6 | I-3 |
| I-4  | Update `_serialize_lane` and `_serialize_track` to accumulate and emit `pitch_bends` (omit when empty) | impl | F-3, F-4, F-6, F-8 | T-17–T-20 |

---

## Open Questions

*(none)*

---

## Open Decisions

*(none)*

---

## Revision Log

### Cycle 1 — Confidence: 72%
- Reconciled: nothing (first cycle, spec created from PRD)
- Added: Q-1 (pitch_bends key presence), Q-2 (consecutive trailing PBs), Q-3 (multi-lane PB support)

### Cycle 2 — Confidence: 93%
- Reconciled: Q-1 → serializer omits `pitch_bends` key when empty (backward-compatible); Q-2 → consecutive-PB rule applies regardless of position, T-14 added; Q-3 → PB allowed per-lane with independent validation, T-15 and T-16 added; T-17 updated to reflect omit-when-empty behaviour
- Added: nothing (confidence ≥ 90%)
