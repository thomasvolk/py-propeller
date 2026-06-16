# Epic 3 · Composition Model — PRD

## Overview

Epic 3 defines the `track()` and `project()` domain objects that assemble note primitives (produced by Epic 1) into a full musical piece. These two factory functions form the compositional backbone of the py-propeller DSL: `track()` groups bars of notes under a named MIDI voice, and `project()` binds one or more tracks together with global playback parameters (BPM and time signature). The resulting objects are pure in-memory Python values with no I/O dependencies, ready to be serialized by Epic 4 and transmitted by Epic 5.

**Confidence Level:** 92% — All core requirements, validation contracts, empty-collection semantics, and immutability policy are fully resolved. Minor residual vagueness: `bpm` is typed as "numeric" without pinning int vs float, and `time_signature` has no validation depth beyond shape (e.g., denominator as power of 2). Both are implementation-time decisions.

---

## User Journeys

### UJ-1 · Composer builds a single-track project

A developer imports `project` and `track` from `propeller`. They construct bars as lists of note primitives from Epic 1 (e.g., `[C4 * 2, D4 * 0.5, E4]`), pass those bars to `track()` along with a name, MIDI channel, and instrument number, then wrap the track in a `project()` call with BPM and time signature. The result is a Python object ready for further processing.

### UJ-2 · Composer assembles a multi-track project

A developer creates several `track()` objects, each with a different name, channel, and instrument. They combine them in a single `project()` call. The project object holds all tracks and global playback parameters in a single inspectable value.

### UJ-3 · Composer inspects the composition structure programmatically

After construction, a developer accesses attributes directly — `p.bpm`, `p.tracks[0].name`, `p.tracks[0].bars[1]` — to verify the structure or to drive downstream logic (e.g., a test assertion or a custom serializer). No special API is required: standard Python attribute access is sufficient.

---

## Functional Requirements

| ID   | Requirement |
|------|-------------|
| F-1  | `track()` accepts keyword arguments `name` (str), `channel` (int), `instrument` (int), and `bars` (list of bars). |
| F-2  | Each bar passed to `track()` is an ordered list of note primitive values (Note or Rest instances) as produced by the Epic 1 DSL. |
| F-3  | `project()` accepts keyword arguments `bpm` (numeric), `time_signature` (2-tuple of ints, e.g. `(4, 4)`), and `tracks` (list of track objects). |
| F-4  | The return value of `track()` exposes all its arguments as readable Python attributes: `.name`, `.channel`, `.instrument`, `.bars`. |
| F-5  | The return value of `project()` exposes all its arguments as readable Python attributes: `.bpm`, `.time_signature`, `.tracks`. |
| F-6  | Individual bars within a track are accessible by index from the track object (e.g., `t.bars[0]`). |
| F-7  | `track` and `project` are importable from the top-level `propeller` package: `from propeller import project, track`. |
| F-8  | Domain objects are implemented as `@dataclass(frozen=True)` classes — immutable Python dataclasses with no hidden magic and no external dependencies. |
| F-9  | The `channel` parameter uses 0-indexed numbering (0–15), matching the raw MIDI wire protocol. |
| F-10 | `track()` raises `PropellerValidationError` immediately on construction if `channel` is outside 0–15 or `instrument` is outside 0–127. |
| F-11 | `project()` raises `PropellerValidationError` immediately on construction if `bpm` is not positive. An empty `tracks=[]` list is valid. |
| F-12 | `PropellerValidationError` is a subclass of `PropellerError`, which is the base exception for the library. |
| F-13 | Validation error messages include bar index and note position where applicable to give precise context. |
| F-14 | `track(bars=[])`, an empty individual bar `[]`, and `project(tracks=[])` are all valid — empty compositions are not errors. |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | The domain model has no I/O, network, or serialization dependencies — it is a pure in-memory representation. |
| NF-2 | All domain objects must produce a human-readable `__repr__` suitable for REPL inspection and test failure messages (provided automatically by `@dataclass`). |
| NF-3 | Domain objects are immutable after construction (`frozen=True`). Post-construction mutation must raise `FrozenInstanceError`. |

---

## Acceptance Criteria

| ID    | Given | When | Then |
|-------|-------|------|------|
| AC-1  | Note primitives `C4`, `D4`, `E4`, `F4` from Epic 1 are available | `track(name="Piano", channel=2, instrument=0, bars=[[C4, D4], [E4, F4]])` is called | The returned object has `.name == "Piano"`, `.channel == 2`, `.instrument == 0`, and `.bars` has length 2 |
| AC-2  | A track object `t` exists | `project(bpm=120, time_signature=(4, 4), tracks=[t])` is called | The returned object has `.bpm == 120`, `.time_signature == (4, 4)`, and `.tracks == [t]` |
| AC-3  | A project `p` with at least one track is constructed | `p.tracks[0].name` is accessed | The track name is returned without error |
| AC-4  | A project `p` is constructed | `repr(p)` is evaluated | The output is a non-empty human-readable string that reflects the project's key structure |
| AC-5  | `from propeller import project, track` is executed in a clean environment | Both names are used to construct a valid project | No import error is raised and both callables work as specified |
| AC-6  | `track()` is called with `channel=16` | Construction is attempted | `PropellerValidationError` is raised immediately |
| AC-7  | `track()` is called with `instrument=128` | Construction is attempted | `PropellerValidationError` is raised immediately |
| AC-8  | `project()` is called with `bpm=0` | Construction is attempted | `PropellerValidationError` is raised immediately |
| AC-9  | `PropellerValidationError` is raised | The exception is inspected | It is a subclass of `PropellerError` and its message is a non-empty descriptive string |
| AC-10 | `track()` is called with `bars=[]` | Construction completes | No error is raised; `.bars` is an empty list |
| AC-11 | `track()` is called with `bars=[[]]` (one empty bar) | Construction completes | No error is raised; `.bars[0]` is an empty list |
| AC-12 | `project()` is called with `tracks=[]` | Construction completes | No error is raised; `.tracks` is an empty list |
| AC-13 | A `Track` object `t` is constructed | `t.name = "Other"` is attempted | `FrozenInstanceError` is raised, confirming immutability |
| AC-14 | A `Project` object `p` is constructed | `p.bpm = 200` is attempted | `FrozenInstanceError` is raised, confirming immutability |

---

## Open Questions

No open questions — all gaps resolved through Cycle 3.

---

## Refinement Log

### Cycle 1 — Confidence: 55%
- Reconciled: nothing (PRD created from scratch this cycle)
- Added: Q1 (bars vs notes parameter name), Q2 (representation type), Q3 (channel numbering), Q4 (validation contract)

### Cycle 2 — Confidence: 82%
- Reconciled: Q1 → F-1, F-4 (`bars=` parameter name); Q2 → F-8 (`@dataclass`); Q3 → F-9 (0-indexed channels 0–15); Q4 → F-10, F-11, F-12, F-13, AC-6, AC-7, AC-8, AC-9 (eager validation via `PropellerValidationError` subclassing `PropellerError`)
- Added: Q5 (empty collection handling), Q6 (dataclass mutability)

### Cycle 3 — Confidence: 92%
- Reconciled: Q5 → F-11 updated (empty `tracks=[]` valid), F-14 added (all empty collections valid), AC-10, AC-11, AC-12 added; Q6 → F-8 updated (`frozen=True`), NF-3 added (immutability contract), AC-13, AC-14 added
- Added: none — PRD is complete
