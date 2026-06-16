# Epic 1 · Note Primitives DSL — PRD

## Overview

Epic 1 defines the building blocks of the py-propeller internal DSL: note constants, duration
modifiers, velocity, and rests. These primitives are the atoms that musicians and developers
manipulate to construct musical sequences. The note constants live in `propeller.notes` and are
designed for star-import use, making musical notation feel natural inside Python code.

Note: the roadmap entry for Epic 1 references `note + amount` / `note - amount` velocity
operators and `(C4 + 30) * 2` as the composition example. These have been superseded by the
briefing update (Q5-A): velocity is now set via a constructor-arg call (`C4(120)`), and the
`+`/`-` operators are removed from the language. The roadmap has not yet been updated to
reflect this.

**Confidence Level:** 92% — All open questions resolved. Residual 8%: Z-callable edge case
(`Z(120)` behaviour) and `note * 0` validation are implicitly handled by Epic 6 F-1 and F-2
but not explicitly stated here; both are implementation-time decisions that do not block
specification.

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

A musician writes `C4(120)` to play middle C at velocity 120, or `C4()` / `C4` for the
default velocity (100). Each form yields a note value that can be used directly in a track.
The original constant is unchanged by calling it.

### UJ-4 · Use a rest

A musician writes `Z` (or `z`) for a one-beat rest, or `Z * 2` for a two-beat rest. Both
forms are interchangeable. The rest is treated as a first-class value that can appear anywhere
a note can, and participates in the same duration modifier syntax.

### UJ-5 · Compose velocity and duration

A musician writes `C4(120) * 2` to produce a note that is both louder and longer. The call
sets the velocity, then `*` sets the duration, producing a single note value with pitch 60,
velocity 120, and duration 2.

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
| F-7  | Note constants are callable. `C4(velocity)` returns a new note with the specified velocity and the same pitch; `C4()` returns a new note with the default velocity (100). In both cases the original constant is unchanged. `C4`, `C4()`, and `C4(100)` are all equivalent representations of middle C at velocity 100. |
| F-8  | `Z` and `z` are first-class rest values with no pitch, a default duration of 1 beat, and no velocity; both are exported from `propeller.notes`. |
| F-9  | `Z * beats` (or `z * beats`) returns a new rest with duration set to `beats`; the original rest constants are unchanged. |
| F-10 | Velocity and duration modifiers are composable: `C4(120) * 2` produces a note with pitch 60, velocity 120, and duration 2. |
| F-11 | All note constants, `Z`, and `z` are exported by `propeller.notes` and are importable via `from propeller.notes import *`. |
| F-12 | Validation of pitch and other construction-time invariants runs at construction time (fail fast); invalid inputs raise `PropellerValidationError`, a subclass of `PropellerError`. |
| F-13 | Calling a note with a velocity outside [0, 127] raises `PropellerValidationError` immediately at call time; no clamping occurs. |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | All note and rest values are immutable; modifier operators and constructor calls always return new objects. |
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
| AC-5  | `C4` imported from `propeller.notes` | `C4(120)` is evaluated | the result has velocity 120 and the original `C4` constant is unchanged |
| AC-6  | `C4` imported from `propeller.notes` | `C4()` is evaluated | the result has velocity 100 (the default) and the original `C4` constant is unchanged |
| AC-7  | `Z` imported from `propeller.notes` | it is used as-is | it represents a rest with no pitch and duration 1 beat |
| AC-8  | `Z` imported from `propeller.notes` | `Z * 2` is evaluated | the result has duration 2 and the original `Z` is unchanged |
| AC-9  | `C4` imported from `propeller.notes` | `C4(120) * 2` is evaluated | the result has pitch 60, velocity 120, and duration 2 |
| AC-10 | `propeller.notes` is imported | every pitch in octaves 0–8 is checked | every such pitch is reachable via at least one named constant |
| AC-11 | `propeller.notes` | `from propeller.notes import *` is executed | only note constants, `Z`, and `z` enter the namespace (no private helpers, no module-level noise) |
| AC-12 | `Df4` imported from `propeller.notes` | it is referenced | it has MIDI pitch 61 (enharmonic with `Cs4`) |
| AC-13 | `from propeller.notes import *` | both `Z` and `z` are referenced | they both represent a rest with no pitch and duration 1 beat |
| AC-14 | `C4` imported from `propeller.notes` | `C4(200)` is evaluated | `PropellerValidationError` is raised with a message naming the field (`velocity`) and the valid range [0, 127] |
| AC-15 | `C4` imported from `propeller.notes` | `C4(-5)` is evaluated | `PropellerValidationError` is raised with a message naming the field (`velocity`) and the valid range [0, 127] |
| AC-16 | `from propeller.notes import *` | `C0` is referenced | it has MIDI pitch 12 |
| AC-17 | `from propeller.notes import *` | `C8` is referenced | it has MIDI pitch 108 |

---

## Open Questions

None — all questions resolved.

---

## Refinement Log

### Cycle 1 — Confidence: 65%
- Reconciled: nothing (PRD created from scratch)
- Added: Q1 (enharmonic naming), Q2 (octave range), Q3 (velocity clamping), Q4 (lowercase z alias)

### Cycle 2 — Confidence: 92%
- Reconciled: Q1 → F-2, AC-12; Q2 → F-2, AC-10, AC-16, AC-17; Q3 → F-7, F-8, F-13, AC-14, AC-15 (silent clamping); Q4 → F-9, F-12, AC-13
- Cross-cutting: PropellerError hierarchy → F-14; construction-time validation → F-14
- AC-10 scope corrected to octaves 0–8
- Added: none (confidence ≥ 90%)

### Cycle 3 — Confidence: 65%
- Context: briefing.md updated; `C4(120)` constructor-arg vs `+`/`-` operator conflict detected.
- UJ-3, UJ-5, F-7, F-8, F-13, AC-5, AC-6, AC-9, AC-14, AC-15 marked pending Q5.
- Added: Q5 (velocity model reconciliation)

### Cycle 4 — Confidence: 82%
- Reconciled: Q5-A → `+`/`-` operators removed; constructor-arg velocity only.
- F-7 replaced: `C4(velocity)` callable. F-8/F-13 (old operators) removed; F-9–F-12 renumbered.
- New F-13 placeholder (pending Q6). UJ-3, UJ-5 rewritten. AC-5, AC-6, AC-9 filled in.
- NF-1 updated to include constructor calls. AC-14, AC-15 remain pending Q6.
- Added: Q6 (out-of-range velocity at call time)

### Cycle 5 — Confidence: 92%
- Reconciled: Q6-A → out-of-range velocity raises `PropellerValidationError` immediately; no clamping.
- F-13 finalised: fail-fast on velocity outside [0, 127].
- AC-14 filled in: `C4(200)` → `PropellerValidationError` naming field and valid range.
- AC-15 filled in: `C4(-5)` → `PropellerValidationError` naming field and valid range.
- Q6 removed from Open Questions.
- Added: none — confidence ≥ 90%; PRD is complete.
