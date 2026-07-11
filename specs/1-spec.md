# 1 · General MIDI Drum Note Constants — Technical Specification

## Overview

Deliver `propeller.notes.drums`, a submodule providing one named `Note`
constant per General MIDI Level 1 percussion sound (MIDI note numbers
35–81), derived from the PRD in `specs/1.md`. Because the target import
path nests under `propeller.notes`, which is currently a single flat
module (`propeller/notes.py`) rather than a package, delivering this epic
also requires converting `propeller/notes.py` into a package so a
`drums` submodule can exist underneath it.

**Confidence Level:** 93% — the structural approach (package conversion),
task breakdown, and data model are all settled; only one low-impact,
internal-only scope choice (whether to retain GM2 source data) remains
open, and it doesn't affect any public behaviour or test outcome.

---

## Architecture Overview

`propeller/notes.py` currently defines `PitchBend`, `Note`, `Rest`, and all
pitch constants (`C4`, `Cs4`, ...) in one file, imported throughout the
codebase as `propeller.notes` (`from propeller.notes import *`,
`import propeller.notes as notes_module`, `from propeller.notes import
Note`, etc. — see `propeller/composition.py`, `propeller/serializer.py`,
and the full `tests/` suite).

To host a `propeller.notes.drums` submodule, `propeller/notes.py` becomes
`propeller/notes/__init__.py` with its content unchanged, so every
existing import path continues to resolve exactly as before.
`propeller/notes/drums.py` is added alongside it as a new submodule.

`drums.py` follows the same generative pattern `notes.py` already uses for
pitch constants: a private, ordered table of `(source name, midi number)`
pairs for the 47 GM1 drum sounds drives a loop that, for each entry,
derives a constant name (strip spaces and hyphens), instantiates a
`propeller.notes.Note` with `pitch=<midi number>` (default `duration` and
`velocity`), assigns it to the module namespace, and appends the name to
`__all__`. GM2-tagged sounds (27–34, 82–87) are never entered into this
table, so they never produce constants.

Reusing `Note` directly (rather than introducing a drum-specific type)
is what makes AC-7 hold for free: a drum constant is a `Note`, so
`Track._validate_lane`'s `isinstance(note, (Note, Rest, PitchBend))` check
already accepts it.

---

## Components

### `propeller/notes/__init__.py` (relocated `notes.py`)

Unchanged in content and behaviour from the current `propeller/notes.py`.
Only its location moves, from a module file to a package's `__init__.py`,
so that `propeller.notes` can have submodules.

### `propeller/notes/drums.py`

New submodule. Responsibilities:
- Hold the private GM1 drum-sound data table (name, MIDI note number) for
  note numbers 35–81, excluding all GM2-tagged sounds.
- Derive each public constant's name from its source name by removing
  spaces and hyphens.
- Instantiate each constant as a `propeller.notes.Note(pitch=<midi
  number>)`.
- Maintain `__all__` listing every generated constant name, mirroring the
  `__all__` pattern already used in `propeller/notes/__init__.py`.

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `propeller.notes.Note` (reused, no new type) | `pitch: int`, `duration: float = 1.0`, `velocity: int = 100` | Every drum constant is a plain instance of this existing dataclass; no drum-specific subclass or wrapper type is introduced. |
| `_DRUM_SOUNDS` (private, `drums.py`) | `list[tuple[str, int]]` — `(source name, midi note number)` | Internal-only table of the 47 GM1 drum sounds (notes 35–81) that drives constant generation. Not part of the public API. |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID   | Task | Type | PRD ref    | Depends on |
|------|------|------|------------|------------|
| T-1  | Confirm the existing `propeller.notes` test suite (`test_notes_module.py`, `test_packaging.py`, `test_pitch_bend.py`, `test_note.py`, `test_ep1_lane_combination.py`, `test_ep2_serializer.py`, `test_composition.py`, `test_time_signature.py`) still specifies the required post-conversion behaviour (star import, `import propeller.notes as x`, individual name imports) with no code changes yet | test | (architecture; enables F-1–F-6) | — |
| I-1  | Convert `propeller/notes.py` into `propeller/notes/__init__.py`, moving its content verbatim | impl | (architecture; enables F-1–F-6) | T-1 |
| T-2  | Add a test asserting `propeller.notes.drums` is importable and defines exactly 47 public constants for MIDI note numbers 35–81 | test | F-1, AC-1 | I-1 |
| I-2  | Create `propeller/notes/drums.py` with the `_DRUM_SOUNDS` table (35–81) and a generation loop producing `Note` instances | impl | F-1, AC-1 | T-2 |
| T-3  | Add a test asserting derived names match source names with spaces removed and resolve to the correct MIDI number (e.g. `BassDrum2 == Note(pitch=35)`) | test | F-2, F-3, AC-2, AC-3 | I-2 |
| I-3  | Implement space-removal name derivation in the generation loop | impl | F-2, F-3, AC-2, AC-3 | T-3 |
| T-4  | Add a test asserting the three hyphenated source names produce hyphen-stripped constants (`ClosedHihat`, `PedalHihat`, `OpenHihat`) resolving to the correct MIDI numbers | test | F-5, AC-6 | I-3 |
| I-4  | Extend name derivation to also strip hyphens | impl | F-5, AC-6 | T-4 |
| T-5  | Add a test asserting none of the 14 GM2 note numbers (27–34, 82–87) or their derived names appear as attributes of `propeller.notes.drums` | test | F-4, AC-4 | I-4 |
| I-5  | Confirm `_DRUM_SOUNDS` contains only the 47 GM1 entries (no GM2 rows to exclude at generation time) | impl | F-4, AC-4 | T-5 |
| T-6  | Add a test asserting a drum constant (e.g. `SnareDrum1`) is a `propeller.notes.Note` instance and can be placed in a `Track.notes` list alongside pitch constants without a validation error | test | F-6, AC-7 | I-5 |
| I-6  | Verify/adjust the generation loop so drum constants are constructed via `propeller.notes.Note(...)` (no separate type) | impl | F-6, AC-7 | T-6 |
| T-7  | Add a test asserting `propeller.notes.drums.__all__` contains exactly the 47 generated constant names and nothing else | test | NF-1, AC-5, AC-8 | I-5 |
| I-7  | Populate `__all__` during generation in `drums.py` | impl | NF-1, AC-5, AC-8 | T-7 |

---

## Open Questions

None this cycle.

---

## Open Decisions

### D-2 · Should GM2-tagged drum data be retained anywhere in the source?

The briefing lists 61 drum sounds total; only the 47 GM1 sounds become
constants. The 14 GM2-tagged entries can be left out of the source
entirely, or kept as unexported data for possible future use.

- [ ] A. Omit GM2 entries entirely — `_DRUM_SOUNDS` only ever contains the 47 GM1 rows *(recommended — matches the PRD scope exactly, no unused/speculative code for a GM2 feature nobody has requested)*
- [ ] B. Retain all 61 entries in a private table tagged with GM level, filtering to GM1 at generation time — keeps the full briefing list as a single source of truth, at the cost of carrying unused data the PRD doesn't ask for

---

## Revision Log

### Cycle 1 — Confidence: 75%
- Initial technical specification derived from `specs/1.md`.
- Added: D-1 (package conversion strategy for `propeller.notes`), D-2 (whether to retain GM2 source data).

### Cycle 2 — Confidence: 93%
- Reconciled: D-1 → Architecture Overview confirmed (package conversion is now the settled approach, not conditional); D-1 removed from Open Decisions.
- Added: none — D-2 remains open but is low-impact; no new questions or decisions needed.
