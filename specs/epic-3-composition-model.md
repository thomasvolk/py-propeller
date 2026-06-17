# Epic 3 · Composition Model — PRD

## Overview

Epic 3 defines the `track()` and `project()` domain objects that assemble note primitives
(produced by Epic 1) into a full musical piece. `track()` groups a flat, ordered sequence of
notes and rests under a named MIDI voice. `project()` binds one or more tracks together with
global playback parameters (BPM, time signature, and bar count). The resulting objects are pure
in-memory Python values with no I/O dependencies, ready to be serialized by Epic 4 and
transmitted by Epic 5.

The track structure has changed relative to the original briefing: a track now carries a flat
`notes=[]` list instead of a `bars=[[…]]` list-of-lists. The project retains an explicit
`bars=N` count that drives the loop length; however, bars as a structural grouping of notes
within a track have been removed.

**Confidence Level:** 87% — All structural changes are reconciled. One gap remains (Q8):
F-12 states that validation error messages include note position "where applicable", but does
not specify what `track()` validates about its `notes` list during construction. Epic 6 F-9
assumes this traversal happens; Epic 3 needs to define its scope.

---

## User Journeys

### UJ-1 · Composer builds a single-track project

A developer imports `project` and `track` from `propeller`. They construct a flat list of note
primitives from Epic 1 (e.g., `[C4(120) * 2, D4() * 0.5, E4()]`) and pass it to `track()`
along with a name, MIDI channel, and instrument number. They then wrap the track in a
`project()` call with BPM, time signature, and a bar count. The result is a Python object
ready for further processing.

### UJ-2 · Composer assembles a multi-track project

A developer creates several `track()` objects, each with a different name, channel, and
instrument. They combine them in a single `project()` call. The project object holds all
tracks and global playback parameters in a single inspectable value.

### UJ-3 · Composer inspects the composition structure programmatically

After construction, a developer accesses attributes directly — `p.bpm`, `p.bars`,
`p.tracks[0].name`, `p.tracks[0].notes[0]` — to verify the structure or to drive downstream
logic (e.g., a test assertion or a custom serializer). No special API is required: standard
Python attribute access is sufficient.

### UJ-4 · Composer writes overlapping notes using multiple lanes

A developer wants a chord or overlapping voices in a single track. They pass a list of lists
as the `notes` argument, where each inner list is an independent lane. Each lane accumulates
its own tick offsets independently, starting from zero. The serializer later merges all lanes
into a single flat notes list, enabling overlapping start-ticks. For example, a C-major chord:
`notes=[[C4()], [E4()], [G4()]]` — three single-note lanes, all starting at tick 0.

---

## Functional Requirements

| ID   | Requirement |
|------|-------------|
| F-1  | `track()` accepts keyword arguments `name` (str), `channel` (int), `instrument` (int), and `notes` — either a flat list of Note or Rest instances (single-lane form) or a list of lists of Note or Rest instances (multi-lane form). |
| F-2  | `project()` accepts keyword arguments `bpm` (numeric), `time_signature` (2-tuple of ints, e.g. `(4, 4)`), `bars` (positive integer — the loop length in bars), and `tracks` (list of track objects). |
| F-3  | The return value of `track()` exposes all its arguments as readable Python attributes: `.name`, `.channel`, `.instrument`, `.notes`. |
| F-4  | The return value of `project()` exposes all its arguments as readable Python attributes: `.bpm`, `.time_signature`, `.bars`, `.tracks`. |
| F-5  | Individual notes within a track are accessible by index from the track object (e.g., `t.notes[0]`). |
| F-6  | `track` and `project` are importable from the top-level `propeller` package: `from propeller import project, track`. |
| F-7  | Domain objects are implemented as `@dataclass(frozen=True)` classes — immutable Python dataclasses with no hidden magic and no external dependencies. |
| F-8  | The `channel` parameter uses 1-indexed numbering (1–16), matching the user-facing MIDI channel convention. |
| F-9  | `track()` raises `PropellerValidationError` immediately on construction if `channel` is outside 1–16 or `instrument` is outside 0–127. |
| F-10 | `project()` raises `PropellerValidationError` immediately on construction if `bpm` is not positive, or if `bars` is not a positive integer. An empty `tracks=[]` list is valid. |
| F-11 | `PropellerValidationError` is a subclass of `PropellerError`, which is the base exception for the library. |
| F-12 | When `track()` constructs, it validates its `notes` list. For the flat (single-lane) form, if an element is not a Note or Rest it raises `PropellerValidationError` with a 1-based position index. For the multi-lane form, the same type check applies to each element of each inner list; the error message includes both the 1-based lane index and the 1-based position within that lane. |
| F-13 | `track(notes=[])` and `project(tracks=[])` are both valid — empty compositions are not errors. |
| F-14 | If `notes` is a flat list (each element is a Note or Rest), the track operates as a single lane. If `notes` is a list of lists (each inner list is a sequence of Note or Rest elements), the track defines multiple independent lanes. The two forms are mutually exclusive and detected automatically: if the first element of `notes` is a list, the multi-lane form is used. An empty `notes=[]` is treated as single-lane. |
| F-15 | In multi-lane form, tick offsets are calculated per lane by the serializer: each lane's tick cursor starts at 0 and advances independently by the cumulative durations within that lane. Empty inner lanes are valid. |

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
| AC-1  | Note primitives `C4`, `D4`, `E4`, `F4` from Epic 1 are available | `track(name="Piano", channel=2, instrument=0, notes=[C4, D4, E4, F4])` is called | The returned object has `.name == "Piano"`, `.channel == 2`, `.instrument == 0`, and `.notes` has length 4 |
| AC-2  | A track object `t` exists | `project(bpm=120, time_signature=(4, 4), bars=2, tracks=[t])` is called | The returned object has `.bpm == 120`, `.time_signature == (4, 4)`, `.bars == 2`, and `.tracks == [t]` |
| AC-3  | A project `p` with at least one track is constructed | `p.tracks[0].name` is accessed | The track name is returned without error |
| AC-4  | A project `p` is constructed | `repr(p)` is evaluated | The output is a non-empty human-readable string that reflects the project's key structure |
| AC-5  | `from propeller import project, track` is executed in a clean environment | Both names are used to construct a valid project | No import error is raised and both callables work as specified |
| AC-6  | `track()` is called with `channel=17` | Construction is attempted | `PropellerValidationError` is raised immediately |
| AC-7  | `track()` is called with `instrument=128` | Construction is attempted | `PropellerValidationError` is raised immediately |
| AC-8  | `project()` is called with `bpm=0` | Construction is attempted | `PropellerValidationError` is raised immediately |
| AC-9  | `project()` is called with `bars=0` | Construction is attempted | `PropellerValidationError` is raised immediately |
| AC-10 | `PropellerValidationError` is raised | The exception is inspected | It is a subclass of `PropellerError` and its message is a non-empty descriptive string |
| AC-11 | `track()` is called with `notes=[]` | Construction completes | No error is raised; `.notes` is an empty list |
| AC-12 | `project()` is called with `tracks=[]` | Construction completes | No error is raised; `.tracks` is an empty list |
| AC-13 | A `Track` object `t` is constructed | `t.name = "Other"` is attempted | `FrozenInstanceError` is raised, confirming immutability |
| AC-14 | A `Project` object `p` is constructed | `p.bpm = 200` is attempted | `FrozenInstanceError` is raised, confirming immutability |
| AC-15 | `track(name="Piano", channel=1, instrument=0, notes=[[C4()], [E4()], [G4()]])` is called | The returned object is inspected | `.notes` has length 3 (number of lanes) and each inner list has length 1 |
| AC-16 | `track(name="Piano", channel=1, instrument=0, notes=[[C4()], []])` is called | Construction completes | No error is raised; empty inner lanes are valid |
| AC-17 | `track()` is called with `notes=[[C4(), "bad"]]` (invalid element in lane 1, position 2) | Construction is attempted | `PropellerValidationError` is raised and the message includes lane and position context |

---

## Open Questions

### Q8 · Scope of track()-level notes validation

`track()` iterates its `notes` list during construction (implied by F-12 and Epic 6 F-9).
What exactly does it validate about each element?

**Options**
- A. Type-only check: each element must be a Note or Rest instance; value ranges (velocity, pitch) are trusted as already validated by Epic 1 at note-creation time. *(recommended — keeps validation layered: Epic 1 owns note correctness, track() owns structural correctness; avoids duplicating range checks that Epic 1 already performs at the point of authoring)*
- B. Type and value check: each element must be a Note or Rest instance AND its pitch and velocity must be within valid MIDI ranges; raises with 1-based position on any failure.
- C. No validation: `track()` does not inspect its `notes` list at all; the list is stored as-is.

**Answer:** A.

---

## Refinement Log

### Cycle 1 — Confidence: 55%
- Reconciled: nothing (PRD created from scratch this cycle)
- Added: Q1 (bars vs notes parameter name), Q2 (representation type), Q3 (channel numbering), Q4 (validation contract)

### Cycle 2 — Confidence: 82%
- Reconciled: Q1 → F-1, F-4 (`bars=` parameter name); Q2 → F-8 (`@dataclass`); Q3 → F-9 (1-indexed channels 1–16); Q4 → F-10, F-11, F-12, F-13, AC-6, AC-7, AC-8, AC-9 (eager validation via `PropellerValidationError` subclassing `PropellerError`)
- Added: Q5 (empty collection handling), Q6 (dataclass mutability)

### Cycle 3 — Confidence: 92%
- Reconciled: Q5 → F-11 updated (empty `tracks=[]` valid), F-14 added (all empty collections valid), AC-10, AC-11, AC-12 added; Q6 → F-8 updated (`frozen=True`), NF-3 added (immutability contract), AC-13, AC-14 added
- Added: none — PRD was complete

### Cycle 4 — Confidence: 55%
- Context: briefing.md updated to drop bar grouping within tracks.
- `track()` parameter renamed from `bars` to `notes`; type changed from list-of-lists to flat list of Note/Rest.
- `project()` `bars` parameter removed; `time_signature` retained.
- All UJs, FRs, and ACs updated to reflect flat `notes` structure.
- F-12 updated: validation error messages reference note position in flat list (not bar+position).
- Added: Q7 (loop length derivation without bars parameter on project)

### Cycle 5 — Confidence: 88%
- Reconciled: Q7-C → `bars=N` restored on `project()` as an explicit loop-length parameter.
  - F-2 updated: `project()` accepts `bars` (positive integer) alongside bpm, time_signature, tracks.
  - F-4 updated: `.bars` added to project readable attributes.
  - F-10 updated: `bars ≤ 0` raises `PropellerValidationError`.
  - AC-2 updated: project AC now asserts `.bars == 2`.
  - AC-9 added: `project(bars=0)` raises `PropellerValidationError`.
  - AC-10–AC-14 renumbered accordingly.
- Note: `bars` on `project()` is a loop-length count; `notes` on `track()` remains a flat list.
- All open questions resolved.

### Cycle 6 — Confidence: 87%
- Reconciled: nothing (no answered questions)
- Gap identified: F-12 stated validation error messages include note position "where applicable" without specifying what track() validates about its notes list. F-12 tightened to name the type-check behaviour explicitly (pending Q8 resolution).
- Added: Q8 (scope of track()-level notes validation: type-only vs type+value vs none)

### Cycle 7 — Confidence: 90%
- Context: briefing.md updated to add multi-lane overlapping notes support.
- UJ-4 added: overlapping notes via multiple lanes.
- F-1 updated: `notes` accepts flat list (single-lane) or list of lists (multi-lane).
- F-12 updated: validation traverses both flat and lane structures; lane error messages include 1-based lane index and position.
- F-14 added: detection rule (first element is list → multi-lane; empty → single-lane).
- F-15 added: tick offsets computed per lane independently by the serializer; empty inner lanes valid.
- AC-15, AC-16, AC-17 added for multi-lane construction and validation.
- No new open questions; Q8 from Cycle 6 still pending (answered as A in spec).
