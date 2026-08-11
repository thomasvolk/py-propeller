# EP-1 · Slide Note Playback — Technical Specification

## Overview
This epic adds a `Slide` note to `propeller.notes` that expands into a sequence of retriggered notes
and pitch-bend events, producing an audible glide between a start pitch and an end pitch when the
composition is serialized to the propeller json format.

**Confidence Level:** 95% — the musical algorithm and the serialization strategy (atomic Slide
expansion, D-1 option A) are both fully pinned down, every F-x/AC-x/NF-1 in the PRD maps to at least
one test/impl task pair in strict TDD order, and no open questions or decisions remain.

---

## Architecture Overview

`Slide` is a new frozen dataclass alongside `Note`, `Rest`, and `PitchBend` in
`propeller/notes/__init__.py`. It carries a start `Note`, an end `Note`, a `steps` size, and a
`duration` (defaulting to `1.0` and settable via `* n`, mirroring `Note`/`Rest`). Unlike `Note`/`Rest`,
`Slide` does not itself get validated field-by-field against MIDI ranges — its job is purely to declare
*intent* (glide from A to B over this duration, at this granularity). All of the actual musical
computation (which whole-tone pitches it passes through, how the total duration divides across them,
how many pitch-bend steps each interval needs) is derived from these four fields on demand.

`Track._validate_lane` (in `propeller/composition.py`) is extended to accept `Slide` as a fourth valid
lane-item type, alongside `Note`, `Rest`, `PitchBend` — it does not need to inspect a Slide's internals,
since a Slide is validated as a single opaque unit and expanded later.

The tick-level expansion — converting a `Slide`'s beat-based description into concrete
`[start_tick, duration_ticks, pitch, velocity]` note rows and `[tick, value]` pitch-bend rows — happens
inside `propeller/serializer.py`, in a new `_expand_slide` function invoked from `_serialize_lane`
exactly where `Note`, `Rest`, and `PitchBend` are already handled. `_expand_slide` computes every
retriggered note's tick/duration and every pitch-bend event's tick directly from the Slide's own
interval math, appends them straight to the lane's `notes_out`/`pitch_bends_out` accumulators, and
advances the lane's shared tick cursor by the Slide's total duration in one step — exactly as if it
were a single, larger `Note`. This atomic-expansion approach was chosen over relaxing `PitchBend`'s
instantaneous semantics or re-articulating a short note per pitch-bend step (see Cycle 1 of the
Revision Log for the alternatives considered and why they were set aside).

This keeps the existing `Note`/`Rest`/`PitchBend` semantics and the "no consecutive PitchBend"
validation rule completely untouched — `Slide` is additive, not a modification of how those types work
elsewhere in the codebase.

---

## Components

### `Slide` (propeller/notes/__init__.py)
A frozen dataclass: `start: Note`, `end: Note`, `steps: float`, `duration: float = 1.0`.

- `__post_init__` validates: `steps` is a positive number no greater than `1.0`; `start` and `end` are
  `Note` instances; `start.pitch != end.pitch` (a zero-distance slide is not meaningful).
- `__mul__` mirrors `Note.__mul__`/`Rest.__mul__`: validates the multiplier is a positive number and
  returns `dataclasses.replace(self, duration=beats)`.
- A pure-computation method (e.g. `intervals()`) returns the ordered list of whole-tone steps between
  `start.pitch` and `end.pitch`: each entry carries the interval's starting pitch, ending pitch, and
  tone-width (`1.0` for a full tone, less than `1.0` for a trailing partial interval). Stepping
  direction follows the sign of `end.pitch - start.pitch`. This method works entirely in musical units
  (pitches, tone-widths) — it has no knowledge of ticks, PPQN, or time signature.

### `Track._validate_lane` (propeller/composition.py)
Extended with one additional accepted type: a lane item may now be a `Note`, `Rest`, `PitchBend`, or
`Slide`. No other validation logic changes.

### `_expand_slide` (propeller/serializer.py, new)
Given a `Slide`, the tick at which it starts, and the track's `denominator`, computes:
- For each interval from `Slide.intervals()`: a time share proportional to its tone-width (so the
  glide's tone-per-time rate is constant across the whole Slide, including a partial final interval).
- One retriggered `Note` per interval, at that interval's starting pitch, using `start.velocity`,
  spanning that interval's time share.
- A sequence of `PitchBend` values within each interval's time share, evenly spaced, in increments no
  larger than `steps`, moving from `0` to the value representing that interval's tone-width against the
  one-tone-equals-full-pitch-bend-range assumption. The number of pitch-bend events is rounded to the
  nearest whole number when the interval's tone-width doesn't divide evenly by `steps`.

Returns the generated note rows, pitch-bend rows, and the Slide's total tick length, so the caller
(`_serialize_lane`) can extend its accumulators and advance the shared cursor exactly once.

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `Slide` | `start: Note`, `end: Note`, `steps: float`, `duration: float = 1.0` | New frozen dataclass in `propeller/notes/__init__.py`; validated in `__post_init__`; `* n` sets `duration` like `Note`/`Rest` |
| `Slide` interval (internal, not a public class) | `start_pitch: int`, `end_pitch: int`, `tone_width: float` | Returned by `Slide.intervals()`; `tone_width == 1.0` except possibly the final interval, which is `< 1.0` when the total distance isn't a whole number of tones |
| `PitchBend` | unchanged | No new fields; `_expand_slide` constructs plain `PitchBend(value)` instances, one per computed step |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID | Task | Type | PRD ref | Depends on |
|----|------|------|---------|------------|
| T-1 | Test `Slide(start, end, steps=value)` constructs with the given fields and `duration` defaulting to `1.0` | test | F-1 | — |
| T-2 | Implement the `Slide` frozen dataclass in `propeller/notes/__init__.py` | impl | F-1 | T-1 |
| T-3 | Test that invalid construction (non-positive/out-of-range `steps`, non-`Note` start/end, `start.pitch == end.pitch`) raises `PropellerValidationError` | test | F-1 | T-2 |
| T-4 | Implement `Slide.__post_init__` validation | impl | F-1 | T-3 |
| T-5 | Test `Slide(...) * n` returns a new `Slide` with `duration=n`, and rejects non-positive/non-numeric `n` | test | F-3, AC-3 | T-4 |
| T-6 | Implement `Slide.__mul__` matching the `Note`/`Rest` pattern | impl | F-3, AC-3 | T-5 |
| T-7 | Test whole-tone interval identification: ascending whole-number-of-tones (C4→C5, 6 intervals), descending (C5→C4), and non-whole-tone (C4→Ds4: one full tone + one half-tone partial final interval) | test | F-2, AC-1, AC-5, AC-8 | T-6 |
| T-8 | Implement `Slide.intervals()` | impl | F-2, AC-1, AC-5, AC-8 | T-7 |
| T-9 | Test each interval's time share is proportional to its tone-width against the Slide's total duration (e.g. the 1.5-tone AC-9 example: two-thirds vs one-third split) | test | F-4, AC-9 | T-8 |
| T-10 | Implement proportional time-share computation from `Slide.intervals()` tone-widths | impl | F-4, AC-9 | T-9 |
| T-11 | Test expansion produces exactly one retriggered `Note` per interval, at that interval's starting pitch, using the Slide's start note's velocity regardless of the end note's velocity | test | F-5, F-9, AC-1, AC-6 | T-10 |
| T-12 | Implement per-interval `Note` generation using start-note velocity | impl | F-5, F-9, AC-1, AC-6 | T-11 |
| T-13 | Test each interval produces evenly-spaced `PitchBend` values from `0` to the interval's tone-width, in increments no larger than `steps`, with the event count rounded to the nearest whole number when it doesn't divide evenly | test | F-6, F-7, F-10, AC-2, AC-7 | T-12 |
| T-14 | Implement per-interval pitch-bend value sequence generation with rounding | impl | F-6, F-7, F-10, AC-2, AC-7 | T-13 |
| T-15 | Test `Track` accepts a `Slide` in a lane (single- and multi-lane form) without raising a validation error | test | F-8, AC-4 | T-14 |
| T-16 | Extend `Track._validate_lane` to accept `Slide` | impl | F-8, AC-4 | T-15 |
| T-17 | Test serializing a track containing a `Slide` produces its generated notes and pitch-bend events at the correct output position and ticks, matching the briefing's full worked example (`Slide(C4, C5, steps=0.1) * 4`) tick-for-tick, and that repeated serialization is deterministic | test | F-8, AC-1, AC-2, AC-4, NF-1 | T-16 |
| T-18 | Implement `_expand_slide` in `propeller/serializer.py` and wire it into `_serialize_lane`'s per-item branch for `Slide` as an atomic unit (no changes to `Note`/`PitchBend`/`Rest` handling) | impl | F-8, AC-1, AC-2, AC-4, NF-1 | T-17 |

---

## Open Questions

None currently — the remaining gap is captured as an architectural decision (D-1) below rather than a
question, since it involves concrete implementation trade-offs rather than a simple choice of desired
behaviour.

---

## Open Decisions

None currently — D-1 was resolved in Cycle 2 (option A, atomic Slide expansion in the serializer).

---

## Revision Log

### Cycle 1 — Confidence: 58%
- Created technical specification from specs/EP-1.md PRD.
- Added: D-1 (how to schedule multiple pitch-bend events within one sustained note's duration) — the
  central architectural question this spec depends on; recommended option A is reflected throughout
  the Architecture Overview, Components, and Implementation Tasks sections above.

### Cycle 2 — Confidence: 95%
- Reconciled: D-1 → option A confirmed (atomic Slide expansion via `_expand_slide` in
  `propeller/serializer.py`, no changes to `Note`/`PitchBend`/`Rest` semantics or the "no consecutive
  PitchBend" rule); Architecture Overview and T-18 updated to state this as settled rather than pending.
- Added: none — specification is complete.
