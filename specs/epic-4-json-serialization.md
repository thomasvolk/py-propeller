# Epic 4 · JSON Serialization — PRD

## Overview

Epic 4 implements the transformation of a composed py-propeller project into the `create-project`
JSON payload required by the propeller-engine socket interface. The serializer is a pure
data-transformation layer: given a project domain object, it returns a Python dict ready to
hand to the transport layer (Epic 2). It has no knowledge of sockets, no network I/O, and no
dependency on the DSL surface. It may be developed against a stub domain model while Epic 3
(Composition Model) is in progress.

The briefing update changes the track structure: each track now carries a flat `.notes` list
instead of a `.bars` list-of-lists. The project retains an explicit `.bars` count (a positive
integer), and `loop_duration` is computed as `project.bars × beats_per_bar × PPQN` — the same
formula as before, but `bars` now comes from the project field rather than from the maximum
track length.

**Confidence Level:** 92% — All domain decisions are fully specified. Residual 8% is Epic 3
integration risk: the `.notes` attribute name on the domain model will be confirmed only once
Epic 3 is complete.

---

## User Journeys

### UJ-1 · Serialize a single-track project

A developer constructs (or stubs) a project object with one track containing a flat sequence of
notes and rests. They pass the project to the serializer and receive back a Python dict whose
structure matches the `create-project` wire format. They inspect the dict, verify the note
tuples, and hand it to the transport layer without further processing.

### UJ-2 · Serialize a project with rests

A developer includes rest values (`Z`) in a track alongside pitched notes. After serialization,
rest entries produce no tuples in the `notes` array; the tick positions of subsequent notes are
correctly offset by the rest duration. The silence is represented implicitly by the gap between
tick positions.

### UJ-3 · Serialize a multi-track project

A developer constructs a project with multiple tracks (e.g., piano on channel 1, bass on
channel 2). The serializer produces a `tracks` list with one entry per track, each with its own
`channel`, `instrument`, and independent `notes` array. All tracks share the same
`loop_duration` in the header.

### UJ-4 · Use stub domain model during parallel development

While Epic 3 is still in progress, a developer defines minimal Python `@dataclass` objects with
the same field names expected from Epic 3. They implement and test the serializer against these
stubs, deferring integration with the real domain model until Epic 3 is complete.

---

## Functional Requirements

| ID  | Requirement |
|-----|-------------|
| F-1 | The serializer exposes a module-level function `serialize(project) -> dict`. |
| F-2 | The returned dict does NOT include a `"command"` key; that envelope is the transport layer's responsibility. |
| F-3 | The returned dict contains a `"header"` dict with keys `"bpm"` (integer) and `"loop_duration"` (integer, in ticks). |
| F-4 | `header.bpm` is taken directly from the project's BPM field. |
| F-5 | `header.loop_duration` is computed as `project.bars × beats_per_bar × PPQN`, where `beats_per_bar` is the numerator of the project's `time_signature` and PPQN is 480. |
| F-6 | The returned dict contains a `"tracks"` list, one entry per track in the project. |
| F-7 | Each track entry is a dict with keys `"name"` (string), `"channel"` (integer, 1–16, 1-indexed), `"instrument"` (integer, 0–127), and `"notes"` (list of 4-element integer arrays). |
| F-8 | Each pitched note maps to a 4-element integer array `[start_tick, duration_ticks, pitch, velocity]`. |
| F-9 | `start_tick` for each note is the cumulative tick offset from the start of the loop (sum of all preceding note and rest durations in ticks within the same track). |
| F-10 | Note and rest durations from the DSL are converted to ticks using a fixed PPQN of 480 ticks per beat. |
| F-11 | Rest values in a track advance the tick cursor but produce no entry in the `notes` array. |
| F-12 | When `beats × PPQN` is not a whole number, the result is rounded to the nearest integer using Python's built-in `round()`. |
| F-13 | The serializer performs no network I/O, file I/O, or other side effects; it is a pure function of its input. |
| F-14 | The serializer has no import dependency on the transport layer (Epic 2). |
| F-15 | The stub domain model used during parallel development consists of Python `@dataclass` objects with the same field names expected from Epic 3: `project.bpm`, `project.time_signature`, `project.bars`, `project.tracks`; `track.name`, `track.channel`, `track.instrument`, `track.notes` (flat list of note/rest objects, each with `.duration_beats`, `.pitch`, and `.velocity` attributes). |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | The serializer is a pure function: identical inputs always produce identical outputs. |
| NF-2 | The serializer imposes no external dependencies beyond the Python standard library. |
| NF-3 | The module can be imported and used without a running propeller-engine daemon. |

---

## Acceptance Criteria

| ID    | Given | When | Then |
|-------|-------|------|------|
| AC-1  | A valid project object with BPM, time signature, bars, and at least one track | `serialize(project)` is called | The return value is a Python `dict` with keys `"header"` and `"tracks"` and no `"command"` key |
| AC-2  | A project with `bpm=120` | `serialize(project)` is called | `result["header"]["bpm"]` equals `120` |
| AC-3  | A project with `bars=1` and `time_signature=(4, 4)` | `serialize(project)` is called | `result["header"]["loop_duration"]` equals `1920` (1 × 4 × 480) |
| AC-4  | A track with two consecutive quarter-note pitches (1 beat each) | `serialize(project)` is called | The first note's `start_tick` is `0`; the second note's `start_tick` is `480` |
| AC-5  | A track containing a one-beat rest followed by a quarter note | `serialize(project)` is called | The `notes` array contains exactly one entry, with `start_tick` equal to `480` |
| AC-6  | A project with two tracks on different channels | `serialize(project)` is called | `result["tracks"]` contains two entries with the correct `channel` values (1-indexed) |
| AC-7  | A note with pitch 60 (C4) and velocity 80 lasting 2 beats | `serialize(project)` is called | The note maps to `[0, 960, 60, 80]` |
| AC-8  | The serializer module | imported in isolation (no socket, no engine) | It imports without error and is callable |
| AC-9  | A project with `bars=3` and `time_signature=(4, 4)` | `serialize(project)` is called | `result["header"]["loop_duration"]` equals `5760` (3 × 4 × 480) |
| AC-10 | A note whose beat duration × 480 is not a whole number (e.g. a triplet `1/3` beat) | `serialize(project)` is called | `duration_ticks` is `round(beats * 480)` (nearest integer, no exception raised) |

---

## Open Questions

*(none — all questions resolved)*

---

## Refinement Log

### Cycle 1 — Confidence: 50%
- Reconciled: none (initial PRD creation)
- Added: Q1 (PPQN resolution), Q2 (loop_duration derivation), Q3 (serializer API shape), Q4 (command key ownership), Q5 (stub domain model contract)

### Cycle 2 — Confidence: 72%
- Reconciled: Q1 → F-10 (fixed 480 PPQN), Q2 → F-5 (time-signature arithmetic for loop_duration), Q3 → F-1 (module-level function), Q4 → F-2 (no command key in serializer output), Q5 → F-14 (dataclass stub model); cross-cutting decisions → F-7 (channels 1-indexed, matching user-facing MIDI convention), F-8 (note tuple [start_tick, duration_ticks, pitch, velocity])
- Added: Q6 (how bars count is obtained for loop_duration), Q7 (rounding policy for fractional beat-to-tick conversion)

### Cycle 3 — Confidence: 92%
- Reconciled: Q6 → F-5 updated (max bar count across tracks; empty-project edge case produces loop_duration=0); Q7 → F-12 added (round() to nearest integer)
- Added: AC-9 (multi-track loop_duration uses longest track), AC-10 (empty project gives loop_duration=0), AC-11 (fractional tick rounding)
- All open questions resolved

### Cycle 4 — Confidence: 50%
- Context: briefing.md updated to drop bar grouping within tracks; `.bars` (list-of-lists) → `.notes` (flat list) on track.
- F-5 rewritten: `loop_duration` derived from total tick sum of longest track (not bar count).
- F-15 stub model updated: `track.notes` flat list.
- AC-3, AC-9, AC-10 rewritten to remove bar-count derivation.
- Added: Q8 (role of time_signature in loop_duration with bars concept removed)

### Cycle 5 — Confidence: 92%
- Reconciled: Q8 (and Epic 3 Q7) → `bars=N` restored on `project()` as an explicit loop-length parameter.
  - F-5 reverted to `project.bars × beats_per_bar × PPQN`; `beats_per_bar = time_signature[0]`.
  - F-15 stub model updated: `project.bars` field added.
  - AC-3 reverted: `bars=1, time_signature=(4,4) → loop_duration = 1920`.
  - AC-9 updated: `bars=3, time_signature=(4,4) → loop_duration = 5760` (replaces track-length-based example).
  - AC-10 removed: "empty project → 0" no longer applies (bars is always a positive integer per Epic 3 validation; tracks=[] with bars=N gives a non-zero loop_duration).
  - AC-10/AC-11 renumbered (old AC-11 fractional tick → new AC-10).
- All open questions resolved.
