# Epic 1 · Note Primitives DSL — PRD

## Overview

Epic 1 defines the building blocks of the py-propeller internal DSL: note constants, duration
modifiers, velocity modifiers, and rests. These primitives are the atoms that musicians and
developers manipulate to construct musical bars. The note constants live in `propeller.notes`
and are designed for star-import use, making musical notation feel natural inside Python code.

**Confidence Level:** 92% — All open questions resolved. Minor residual gaps: the module
location of `PropellerError`/`PropellerValidationError` is not yet specified, and whether `z`
is the same object as `Z` (identity) or merely equal (equality) is left to the implementer.
Neither gap blocks implementation.

---

## User Journeys

### UJ-1 · Import and play a named note

A musician opens a Python file, writes `from propeller.notes import *`, and immediately
references `C4`, `Cs4`, and `Ef4` without any additional setup. Each constant is ready to use
as a note value with a pitch, a default duration of 1 beat, and a default velocity of 100.

### UJ-2 · Adjust note duration

A musician writes `C4 * 2` to hold middle C for two beats, and `D4 * 0.5` to play D4 as a
quaver (half a beat). The original `C4` constant is unaffected; the expression produces a new
note value with the updated duration.

### UJ-3 · Adjust note velocity

A musician writes `C4 + 30` to accent a note and `C4 - 20` to soften one. The original
constant is unchanged; each expression yields a new note value. Values that would exceed [0, 127]
are clamped silently — no exception is raised.

### UJ-4 · Use a rest

A musician writes `Z` (or `z`) for a one-beat rest, or `Z * 2` for a two-beat rest. Both
forms are interchangeable. The rest is treated as a first-class value that can appear anywhere
a note can, and participates in the same duration modifier syntax.

### UJ-5 · Compose modifiers

A musician writes `(C4 + 30) * 2` to produce a note that is both louder and longer. Velocity
is applied first, then duration, producing a single note value with pitch 60, velocity 130, and
duration 2.

---

## Functional Requirements

| ID   | Requirement |
|------|-------------|
| F-1  | Note constants are named by pitch class letter, optional accidental suffix, and octave number (e.g. `C4`, `Cs4` for C-sharp, `Ef4` for E-flat). |
| F-2  | Note constants cover octaves 0–8 (C0 through C8), providing both sharp (`s`) and flat (`f`) spellings for every enharmonically equivalent semitone: `Cs`/`Df`, `Ds`/`Ef`, `Fs`/`Gf`, `Gs`/`Af`, `As`/`Bf`. |
| F-3  | Each note constant has an immutable MIDI pitch value in the range 0–127. |
| F-4  | The default duration of a note is 1 beat. |
| F-5  | The default velocity of a note is 100. |
| F-6  | `note * beats` returns a new note with duration set to `beats`; the original is unchanged. |
| F-7  | `note + amount` returns a new note with velocity increased by `amount`, clamped silently to [0, 127]; the original is unchanged. |
| F-8  | `note - amount` returns a new note with velocity decreased by `amount`, clamped silently to [0, 127]; the original is unchanged. |
| F-9  | `Z` and `z` are first-class rest values with no pitch, a default duration of 1 beat, and no velocity; both are exported from `propeller.notes`. |
| F-10 | `Z * beats` (or `z * beats`) returns a new rest with duration set to `beats`; the original rest constants are unchanged. |
| F-11 | Modifier operators are composable left-to-right: `(C4 + 30) * 2` produces a note with pitch 60, velocity 130, and duration 2. |
| F-12 | All note constants, `Z`, and `z` are exported by `propeller.notes` and are importable via `from propeller.notes import *`. |
| F-13 | Out-of-range velocity values produced by `+` or `-` are clamped silently to [0, 127]; no exception is raised. |
| F-14 | Validation of pitch and other construction-time invariants runs at construction time (fail fast); invalid inputs raise `PropellerValidationError`, a subclass of `PropellerError`. |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | All note and rest values are immutable; modifier operators always return new objects. |
| NF-2 | The `propeller.notes` module has no external dependencies — pure Python only. |
| NF-3 | Importing `propeller.notes` must have no observable side effects. |

---

## Acceptance Criteria

| ID    | Given | When | Then |
|-------|-------|------|------|
| AC-1  | `from propeller.notes import *` | `C4` is referenced | it has MIDI pitch 60 |
| AC-2  | `from propeller.notes import *` | `Cs4` is referenced | it has MIDI pitch 61 |
| AC-3  | `from propeller.notes import *` | `Ef4` is referenced | it has MIDI pitch 63 |
| AC-4  | a note constant with default duration 1 | `note * 2` is evaluated | the result has duration 2 and the original constant is unchanged |
| AC-5  | a note constant with default velocity 100 | `note + 30` is evaluated | the result has velocity 130 and the original constant is unchanged |
| AC-6  | a note constant with default velocity 100 | `note - 20` is evaluated | the result has velocity 80 and the original constant is unchanged |
| AC-7  | `Z` imported from `propeller.notes` | it is used as-is | it represents a rest with no pitch and duration 1 beat |
| AC-8  | `Z` imported from `propeller.notes` | `Z * 2` is evaluated | the result has duration 2 and the original `Z` is unchanged |
| AC-9  | the expression `(C4 + 30) * 2` | it is evaluated | the result has pitch 60, velocity 130, and duration 2 |
| AC-10 | `propeller.notes` is imported | every pitch in octaves 0–8 is checked | every such pitch is reachable via at least one named constant |
| AC-11 | `propeller.notes` | `from propeller.notes import *` is executed | only note constants, `Z`, and `z` enter the namespace (no private helpers, no module-level noise) |
| AC-12 | `Df4` imported from `propeller.notes` | it is referenced | it has MIDI pitch 61 (enharmonic with `Cs4`) |
| AC-13 | `from propeller.notes import *` | both `Z` and `z` are referenced | they both represent a rest with no pitch and duration 1 beat |
| AC-14 | a note constant with default velocity 100 | `note - 200` is evaluated | the result has velocity 0 (clamped, no exception raised) |
| AC-15 | a note constant with default velocity 100 | `note + 300` is evaluated | the result has velocity 127 (clamped, no exception raised) |
| AC-16 | `from propeller.notes import *` | `C0` is referenced | it has MIDI pitch 12 |
| AC-17 | `from propeller.notes import *` | `C8` is referenced | it has MIDI pitch 108 |

---

## Open Questions

None — all questions resolved in Cycle 2.

---

## Refinement Log

### Cycle 1 — Confidence: 65%
- Reconciled: nothing (PRD created from scratch)
- Added: Q1 (enharmonic naming), Q2 (octave range), Q3 (velocity clamping), Q4 (lowercase z alias)

### Cycle 2 — Confidence: 92%
- Reconciled: Q1 → F-2, AC-12 (all enharmonic pairs exported); Q2 → F-2, AC-10, AC-16, AC-17 (octaves 0–8, C0=MIDI 12, C8=MIDI 108); Q3 → F-7, F-8, F-13, AC-14, AC-15 (silent velocity clamping); Q4 → F-9, F-12, AC-13 (both Z and z exported as rests)
- Cross-cutting applied: exception hierarchy PropellerError/PropellerValidationError → F-14; validation at construction time → F-14; MIDI channels 0-indexed noted (no Epic 1 requirement affected)
- AC-10 corrected: scope changed from "every MIDI note number 0–127" to "every pitch in octaves 0–8" to align with F-2
- Added: none (confidence ≥ 90%)
