# EP-1 · Time Signature Governs Bar Length — PRD

## Overview

A composer sets a time signature as a pair of numbers, and the system uses both numbers
to determine how a bar is measured: the first number is how many beats make up one bar,
and the second number is which note value counts as one beat. Once set, the time signature
changes how many notes of a given duration are needed to fill a bar, and this is observable
in the resulting composition — it is no longer ignored.

**Confidence Level:** 95% — all three open questions from Cycle 1 are resolved with a
generalized beat-unit rule, a no-cross-validation stance on `bars`, and serialization as the
sole verification surface. The remaining 5% reflects unspecified rounding behavior for
denominators that don't evenly divide four quarter notes (e.g. `denominator=6`), which is a
minor edge case not covered by the briefing's examples.

---

## User Journeys

### UJ-1 · Composer writes a bar in a non-4/4 meter

A composer sets `time_signature=(3, 4)` on a `Project` and writes a track whose notes'
durations sum to 3 beats. When the composition is played or exported, that material occupies
exactly one bar — not the 4-beat bar implied by the old, ignored default.

### UJ-2 · Composer switches the beat unit via the denominator

A composer sets `time_signature=(8, 8)` (bar = 8 eighth-note beats) and writes
`C4 * 8` — eight consecutive unit-duration notes. The composer expects this to fill exactly
one bar, the same way `C4 * 4` fills one bar under `time_signature=(4, 4)`. The perceived
tempo of individual notes also changes: under `(x, 8)` a unit-duration note plays for the
duration of an eighth note, not a quarter note, so switching from `(4, 4)` to `(4, 8)` at the
same bpm makes each written note play twice as fast in real time.

---

## Functional Requirements

| ID  | Requirement |
|-----|-------------|
| F-1 | Setting a `Project`'s `time_signature=(numerator, denominator)` determines that one bar contains `numerator` beats. |
| F-2 | The `denominator` of the time signature determines which note value (quarter note when `denominator=4`, eighth note when `denominator=8`) is counted as one beat. |
| F-3 | A note or rest written with a unit duration multiplier (e.g. `C4 * 1`) has a real-world duration equal to one beat as defined by the current time signature's denominator, not a fixed quarter note. |
| F-4 | `numerator` consecutive unit-duration notes (e.g. `C4 * numerator`) exactly fill one bar under the current time signature. |
| F-5 | Changing the time signature on a `Project` changes where bar boundaries fall and how long unit-duration notes last, compared to leaving it at its previous value — the setting is no longer inert. |
| F-6 | The beat unit generalizes to any positive integer `denominator`: one beat is worth `4 / denominator` quarter notes (e.g. `denominator=16` → sixteenth-note beat, `denominator=2` → half-note beat), not just the `4` and `8` cases shown in the briefing. |
| F-7 | `Project.bars` remains purely informational: the system does not validate or reject a track whose total note duration under- or over-fills `bars * numerator` beats. |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | Time signature handling must apply uniformly across every consumer of note timing (serialization output and playback), so the two never disagree about how long a bar or a beat is. |
| NF-2 | Playback must derive its timing from the same serialized tick data verified by this epic's acceptance criteria, rather than an independent timing computation, so serialization-level correctness is sufficient to guarantee playback correctness. |

---

## Acceptance Criteria

| ID   | Given | When | Then |
|------|-------|------|------|
| AC-1 | A `Project` with `time_signature=(4, 4)` and a track containing `C4 * 4` | the composition is serialized | the four notes exactly fill one bar, each occupying the duration of a quarter note |
| AC-2 | A `Project` with `time_signature=(8, 8)` and a track containing `C4 * 8` | the composition is serialized | the eight notes exactly fill one bar, each occupying the duration of an eighth note |
| AC-3 | A `Project` with `time_signature=(4, 8)` and a track containing `C4 * 4` | the composition is serialized | the four notes exactly fill one bar, each occupying the duration of an eighth note |
| AC-4 | A `Project` with `time_signature=(8, 4)` and a track containing `C4 * 8` | the composition is serialized | the eight notes exactly fill one bar, each occupying the duration of a quarter note |
| AC-5 | Two otherwise-identical compositions differing only in `time_signature` | each is serialized | the resulting bar boundaries and/or total durations differ between the two, demonstrating the setting has an effect |
| AC-6 | A `Project` with `time_signature=(numerator, 16)` and a track containing `numerator` consecutive unit-duration notes | the composition is serialized | the notes exactly fill one bar, each occupying the duration of a sixteenth note |

---

## Open Questions

None outstanding.

---

## Refinement Log

### Cycle 1 — Confidence: 55%
- Created PRD from specs/roadmap.md EP-1 entry; grounded functional requirements against current implementation in propeller/composition.py, propeller/serializer.py, and propeller/notes.py, which confirmed time_signature is validated but never consumed beyond `beats_per_bar` in loop_duration.
- Added: Q1 (unit-duration meaning for denominators beyond 4/8), Q2 (bars/content cross-validation), Q3 (verification scope: serialization vs. playback)

### Cycle 2 — Confidence: 95%
- Reconciled: Q1 → F-6 (general beat-unit formula for any positive integer denominator), AC-6 (denominator=16 case)
- Reconciled: Q2 → F-7 (`bars` stays purely informational, no cross-validation)
- Reconciled: Q3 → NF-2 (playback derives timing from the same serialized ticks); AC-1..AC-5 narrowed to "serialized" as the verification surface
- Added: none — no unresolved gaps remain beyond a minor rounding edge case noted in the Confidence Level explanation
