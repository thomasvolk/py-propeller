# EP-1 · Pitch Bend Lane Combination — Technical Specification

## Overview

Fix the multi-lane serializer so that pitch bends in PB-only lanes (lanes containing
only `PB` and `Z` elements) are included in the output at their correct tick offsets.
The change also handles PB-only lanes with multiple pitch bends and rejects tracks where
two lanes produce a pitch bend at the same tick. All existing single-lane behaviour is
preserved unchanged.

**Confidence Level:** 95% — all PRD requirements have covering tasks, TDD order is
intact, and no open decisions remain.

---

## Architecture Overview

All changes are confined to `propeller/serializer.py`. No other module is touched.

**Root cause.** `_serialize_lane` uses a "pending PB" pattern: a `PitchBend` element
sets a pending value, which is flushed to output only when the next `Note` is processed.
If the lane ends before a `Note` appears — as is always the case for a PB-only lane —
the pending value is silently discarded. This is the existing "trailing PB discarded"
rule (test T-19), which is correct for single-lane tracks but wrong for PB-only lanes in
a multi-lane context.

**Two changes to `_serialize_lane`:**

1. **`emit_trailing_pb` parameter** (default `False`): when `True`, any pending PB
   remaining at end-of-lane is appended to the output instead of discarded. The
   single-lane call site continues to pass the default, so T-19 behaviour is preserved.
   The multi-lane call site passes `True`.

2. **Intermediate PB flush**: when a new `PitchBend` is encountered while a pending PB
   already exists (possible in multi-PB PB-only lanes like `[PB(0.1), Z, PB(0.5), Z]`),
   the existing pending PB is flushed to output before the new one is stored. Without
   this, intermediate PBs are silently overwritten.

**One change to `_serialize_track`:**

- The multi-lane path calls `_serialize_lane(lane, emit_trailing_pb=True)` for each
  lane.
- After collecting all pitch bends from all lanes, it checks for duplicate tick offsets.
  If any two PBs share the same tick, `PropellerValidationError` is raised at
  serialization time. This keeps all tick-aware logic inside the serializer and avoids
  duplicating tick-offset accumulation in `composition.py`.

The single-lane path in `_serialize_track` is unchanged.

---

## Components

### `_serialize_lane(lane, emit_trailing_pb=False)`

Returns `(notes_out, pitch_bends_out)`. Modified behaviour:

- When a `PitchBend` is encountered and a pending PB already exists, the pending PB is
  flushed to `pitch_bends_out` before the new one is stored.
- When the lane ends and `emit_trailing_pb` is `True`, any remaining pending PB is
  flushed to `pitch_bends_out`.
- All other behaviour (tick cursor advancement, note collection, Rest handling) is
  unchanged.

### `_serialize_track(track)`

Modified multi-lane path only:

- Calls `_serialize_lane(lane, emit_trailing_pb=True)` instead of `_serialize_lane(lane)`.
- After the loop, checks whether any two entries in `all_pitch_bends` share the same
  tick offset; raises `PropellerValidationError` if so.
- Sort and deduplication logic is unchanged.

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `PitchBend` | `value: float` | Unchanged. Range `[-1.0, 1.0]`. |
| `Note` | `pitch, duration, velocity` | Unchanged. |
| `Rest` | `duration` | Unchanged. |
| pitch-bend entry | `[tick: int, midi_value: int]` | Unchanged output format. `midi_value = int(round((value + 1) / 2 * 16383))`. |

No new types are introduced.

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID   | Task | Type | PRD ref | Depends on |
| ---- | ---- | ---- | ------- | ---------- |
| T-01 | Write test: `_serialize_lane([Z, PB(0.5)], emit_trailing_pb=True)` returns `([], [[480, 12287]])` | test | F-1 | — |
| T-02 | Impl: add `emit_trailing_pb=False` param to `_serialize_lane`; flush pending PB at end-of-lane when `True` | impl | F-1 | T-01 |
| T-03 | Write test: multi-lane `_serialize_track` with a PB-only lane `[Z, PB(0.5)]` includes `[480, 12287]` in `pitch-bends` | test | F-1, F-2 | — |
| T-04 | Impl: update multi-lane path in `_serialize_track` to call `_serialize_lane(lane, emit_trailing_pb=True)` | impl | F-1, F-2 | T-03, T-02 |
| T-05 | Write test: `_serialize_lane([PB(0.1), Z, PB(0.5), Z], emit_trailing_pb=True)` returns `([], [[0, 9011], [480, 12287]])` | test | F-7, AC-7 | — |
| T-06 | Impl: flush pending PB in `_serialize_lane` when a new `PitchBend` is encountered while a pending PB exists | impl | F-7 | T-05, T-02 |
| T-07 | Write test: `_serialize_track` raises `PropellerValidationError` when two lanes each produce a PB at tick 0 | test | F-6, AC-6 | — |
| T-08 | Impl: after collecting all lane PBs in multi-lane path, detect duplicate tick offsets and raise `PropellerValidationError` | impl | F-6 | T-07, T-04 |
| T-09 | Write integration test: full project with lanes `[PB(0.0), D4 * 4]` and `[Z, PB(0.5)]` at 80 BPM, 4/4, 2 bars serializes to `pitch-bends: [[0, 8192], [480, 12287]]` (AC-1) | test | AC-1 | — |
| T-10 | Write test: PB-only lane `[Z, PB(0.5)]` alongside a note-bearing lane contributes zero note entries to the output (AC-3) | test | F-3, F-4, AC-3 | — |
| T-11 | Write test: when PBs from two lanes arrive out of tick order, the merged `pitch-bends` array is sorted ascending (AC-2) | test | F-2, AC-2 | — |
| T-12 | Regression: run full existing test suite; confirm T-19 (single-lane trailing PB discarded) and T-20 (no-PB track has no key) still pass (NF-1, AC-4, AC-5) | test | NF-1, AC-4, AC-5 | T-04, T-06, T-08 |

---

## Open Questions

*No open questions.*

---

## Open Decisions

*No open decisions.*

---

## Revision Log

### Cycle 1 — Confidence: 80%
- Reconciled: nothing (EP-1-spec.md did not previously exist)
- Added: D-1 (collision detection timing — serialization vs. construction)

### Cycle 2 — Confidence: 95%
- Reconciled: D-1 (A) → serialization-time detection confirmed; Architecture Overview updated to remove pending-decision note; no new tasks needed (T-07/T-08 already cover this)
- Added: nothing — specification is complete
