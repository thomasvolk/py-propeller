# EP-1 · Time Signature Governs Bar Length — Technical Specification

## Overview

This epic makes `Project.time_signature` actually govern timing: the numerator determines
how many beats fill a bar, and the denominator determines which note value counts as one
beat. Both numbers currently flow into `Project` validation but are otherwise dropped on
the floor before reaching the serialized MIDI-tick output that both file export and live
playback consume.

**Confidence Level:** 96% — PRD coverage, TDD task ordering, architecture, and the rounding
strategy for non-divisor denominators are all pinned down. No open questions or decisions
remain; the residual 4% reflects normal implementation risk rather than a specified gap.

---

## Architecture Overview

All timing math for note/rest duration and bar length already funnels through exactly one
place: `propeller/serializer.py`. `propeller/player.py` never computes timing itself — every
branch of `play()` calls `serialize(project)` and forwards the resulting JSON payload
verbatim to either stdout or `PropellerClient`. `propeller/composition.py` validates that
`time_signature` is a two-element tuple of positive integers but performs no timing
computation with it. This means PRD requirements F-1 through F-6 (beat/bar timing) and NF-1/
NF-2 (uniform timing across serialization and playback) are satisfiable by changing
`propeller/serializer.py` alone — no changes to `propeller/composition.py`,
`propeller/player.py`, `propeller/transport.py`, or `propeller/notes.py` are needed.

Today, `serializer.py` hardcodes two assumptions that must change:

1. `_beats_to_ticks(beats)` converts a duration multiplier straight to ticks via
   `round(beats * PPQN)`, treating one duration-unit as always equal to one quarter note
   (`PPQN` ticks), regardless of `time_signature`.
2. `serialize()` computes `loop_duration = project.bars * beats_per_bar * PPQN`, using only
   the numerator (`beats_per_bar`) and the fixed `PPQN`, ignoring the denominator entirely.

Both must instead derive from the same formula, per PRD F-2/F-3/F-6: one beat is worth
`4 / denominator` quarter notes, i.e. `PPQN * 4 / denominator` ticks. Per D-1 (resolved,
option B), this formula is applied with a single rounding step at each site that needs a
tick count — `round(beats * PPQN * 4 / denominator)` for a note/rest duration, and
`round(bars * numerator * PPQN * 4 / denominator)` for `loop_duration` — rather than
pre-rounding an intermediate ticks-per-beat constant and rounding again on top of it. This
avoids compounding rounding error for denominators that don't evenly divide `PPQN * 4`
(e.g. `denominator=7`), while producing identical results to a pre-rounded constant for the
denominators this epic's ACs test (4, 8, 16), which all divide `PPQN * 4` evenly.

`Project.bars` remains purely informational per PRD F-7: no cross-validation is added
between note content and `bars * numerator`.

---

## Components

### `propeller/serializer.py` — tick conversion

- `_beats_to_ticks(beats, time_signature)` is updated to compute
  `round(beats * PPQN * 4 / time_signature[1])` directly (single rounding step per call,
  per resolved D-1) instead of `round(beats * PPQN)`.
- `_serialize_lane` and `_serialize_track` pass `time_signature` through to
  `_beats_to_ticks` so every note and rest in every lane/track is converted consistently.

### `propeller/serializer.py` — bar length

- `serialize()`'s `loop_duration` calculation is updated to
  `round(project.bars * project.time_signature[0] * PPQN * 4 / project.time_signature[1])`
  (single rounding step, consistent with the note/rest conversion above), replacing
  `project.bars * beats_per_bar * PPQN`, so total loop length agrees with per-note tick
  placement under any time signature.

### `propeller/player.py`, `propeller/composition.py` — unchanged

No code changes. Their existing behaviour (delegating all timing to `serialize()`,
validating only tuple shape/positivity of `time_signature`) already satisfies NF-1, NF-2,
and F-7. Existing tests (`tests/test_player.py`, `tests/test_composition.py`) continue to
pin this and do not need new cases for this epic.

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| *(none — no dataclass changes)* | — | `Project`, `Track`, `Note`, `Rest`, `PitchBend` are unchanged. No intermediate ticks-per-beat value is stored or passed around; `propeller/serializer.py` applies `PPQN * 4 / time_signature[1]` inline, with a single rounding step, at each site that needs a tick count (per resolved D-1). |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID   | Task | Type | PRD ref | Depends on |
|------|------|------|---------|------------|
| T-1  | Test: a unit-duration note under `time_signature=(4, 4)` serializes to 480 ticks (one quarter note) | test | F-2, F-3, AC-1 | — |
| T-2  | Test: a unit-duration note under `time_signature=(8, 8)` serializes to 240 ticks (one eighth note) | test | F-2, F-3, AC-2 | — |
| T-3  | Test: a unit-duration note under `time_signature=(numerator, 16)` serializes to 120 ticks (one sixteenth note), confirming the `4/denominator` formula generalizes beyond 4 and 8 | test | F-6, AC-6 | — |
| I-1  | Implement time-signature-aware tick conversion in `propeller/serializer.py`: update `_beats_to_ticks` to `round(beats * PPQN * 4 / denominator)` and thread `time_signature` through `_serialize_lane`/`_serialize_track`, replacing the fixed-`PPQN` conversion | impl | F-2, F-3, F-6 | T-1, T-2, T-3 |
| T-4  | Test: `C4 * 4` under `(4, 4)` produces notes whose total tick span exactly equals one bar | test | F-4, AC-1 | I-1 |
| T-5  | Test: `C4 * 8` under `(8, 8)` produces notes whose total tick span exactly equals one bar | test | F-4, AC-2 | I-1 |
| T-6  | Test: `C4 * 4` under `(4, 8)` produces notes whose total tick span exactly equals one bar | test | F-4, AC-3 | I-1 |
| T-7  | Test: `C4 * 8` under `(8, 4)` produces notes whose total tick span exactly equals one bar | test | F-4, AC-4 | I-1 |
| I-2  | Update `serialize()`'s `loop_duration` calculation to `round(bars * numerator * PPQN * 4 / denominator)`, replacing `bars * numerator * PPQN` | impl | F-1, F-4 | T-4, T-5, T-6, T-7 |
| T-8  | Test: two otherwise-identical projects differing only in `time_signature` produce different serialized tick output (note positions and/or `loop_duration`) | test | F-5, AC-5 | I-2 |
| T-9  | Test: a track whose note durations under- or over-fill `bars * numerator` beats under a non-`(4, 4)` time signature still serializes without raising a validation error | test | F-7 | I-2 |
| T-10 | Test (regression): `propeller/player.py`'s dry-run (`-n`) output under a non-`(4, 4)` time signature matches a direct `serialize()` call, confirming no independent playback timing path was introduced | test | NF-1, NF-2 | I-2 |

---

## Open Questions

None outstanding.

---

## Open Decisions

None outstanding.

---

## Revision Log

### Cycle 1 — Confidence: 82%
- Created spec from specs/EP-1.md; grounded architecture against current implementation of `propeller/serializer.py` (`_beats_to_ticks`, `_serialize_lane`, `serialize`) and confirmed `propeller/player.py` and `propeller/composition.py` require no changes, satisfying NF-1/NF-2/F-7 structurally.
- Added: D-1 (rounding strategy for denominators that don't evenly divide `PPQN * 4`)

### Cycle 2 — Confidence: 96%
- Reconciled: D-1 → option B selected (single-round-per-site formula); updated Architecture Overview, both Components subsections, Data Model note, and tasks I-1/I-2 to specify `round(beats * PPQN * 4 / denominator)` and `round(bars * numerator * PPQN * 4 / denominator)` directly, with no intermediate pre-rounded ticks-per-beat constant.
- Added: none — no open questions or decisions remain
