# Epic 4 · JSON Serialization — PRD

## Overview

Epic 4 belongs to Stream 2 (Engine Connectivity), Phase 2. It implements the transformation of a composed py-propeller project into the `create-project` JSON payload required by the propeller-engine socket interface. The serializer is a pure data-transformation layer: given a project domain object, it returns a Python dict ready to hand to the transport layer (Epic 2). It has no knowledge of sockets, no network I/O, and no dependency on the DSL surface. It may be developed against a stub domain model while Epic 3 (Composition Model) is in progress.

**Confidence Level:** 92% — All domain decisions are fully specified (PPQN, loop_duration formula with max-bar-count and empty-project edge case, rounding policy, API shape, command-key ownership, stub model contract, channel indexing, note tuple layout). Residual 8% is Epic 3 integration risk: the `.bars` attribute name on the domain model will be confirmed only once Epic 3 progresses.

---

## User Journeys

### UJ-1 · Serialize a single-track project

A developer constructs (or stubs) a project object with one track containing a sequence of bars. They pass the project to the serializer and receive back a Python dict whose structure matches the `create-project` wire format. They inspect the dict, verify the note tuples, and hand it to the transport layer without further processing.

### UJ-2 · Serialize a project with rests

A developer includes rest values (`Z`) in a bar alongside pitched notes. After serialization, rest entries produce no tuples in the `notes` array; the tick positions of subsequent notes are correctly offset by the rest duration. The silence is represented implicitly by the gap between tick positions.

### UJ-3 · Serialize a multi-track project

A developer constructs a project with multiple tracks (e.g., piano on channel 1, bass on channel 2). The serializer produces a `tracks` list with one entry per track, each with its own `channel`, `instrument`, and independent `notes` array. All tracks share the same `loop_duration` in the header.

### UJ-4 · Use stub domain model during parallel development

While Epic 3 is still in progress, a developer defines minimal Python `@dataclass` objects with the same field names expected from Epic 3. They implement and test the serializer against these stubs, deferring integration with the real domain model until Epic 3 is complete.

---

## Functional Requirements

| ID  | Requirement |
|-----|-------------|
| F-1 | The serializer exposes a module-level function `serialize(project) -> dict`. |
| F-2 | The returned dict does NOT include a `"command"` key; that envelope is the transport layer's responsibility. |
| F-3 | The returned dict contains a `"header"` dict with keys `"bpm"` (integer) and `"loop_duration"` (integer, in ticks). |
| F-4 | `header.bpm` is taken directly from the project's BPM field. |
| F-5 | `header.loop_duration` is computed as `bars × beats_per_bar × PPQN`, where `bars = max(len(t.bars) for t in project.tracks)` (longest track), `beats_per_bar` is the numerator of the project's time signature, and PPQN is 480. If all tracks are empty, `loop_duration` is 0. |
| F-6 | The returned dict contains a `"tracks"` list, one entry per track in the project. |
| F-7 | Each track entry is a dict with keys `"name"` (string), `"channel"` (integer, 0–15, 0-indexed), `"instrument"` (integer, 0–127), and `"notes"` (list of 4-element integer arrays). |
| F-8 | Each pitched note maps to a 4-element integer array `[start_tick, duration_ticks, pitch, velocity]`. |
| F-9 | `start_tick` for each note is the cumulative tick offset from the start of the loop (sum of all preceding note and rest durations in ticks). |
| F-10 | Beat durations from the DSL are converted to ticks using a fixed PPQN of 480 ticks per beat. |
| F-11 | Rest values in a bar advance the tick cursor but produce no entry in the `notes` array. |
| F-12 | When `beats × PPQN` is not a whole number, the result is rounded to the nearest integer using Python's built-in `round()`. |
| F-13 | The serializer performs no network I/O, file I/O, or other side effects; it is a pure function of its input. |
| F-14 | The serializer has no import dependency on the transport layer (Epic 2). |
| F-15 | The stub domain model used during parallel development consists of Python `@dataclass` objects with the same field names expected from Epic 3. |

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
| AC-1  | A valid project object with BPM, time signature, and at least one track | `serialize(project)` is called | The return value is a Python `dict` with keys `"header"` and `"tracks"` and no `"command"` key |
| AC-2  | A project with `bpm=120` | `serialize(project)` is called | `result["header"]["bpm"]` equals `120` |
| AC-3  | A project with 1 bar of 4/4 time | `serialize(project)` is called | `result["header"]["loop_duration"]` equals `1920` (1 × 4 × 480) |
| AC-4  | A track with two consecutive quarter-note pitches (1 beat each) | `serialize(project)` is called | The first note's `start_tick` is `0`; the second note's `start_tick` is `480` |
| AC-5  | A track containing a one-beat rest followed by a quarter note | `serialize(project)` is called | The `notes` array contains exactly one entry, with `start_tick` equal to `480` |
| AC-6  | A project with two tracks on different channels | `serialize(project)` is called | `result["tracks"]` contains two entries with the correct `channel` values (0-indexed) |
| AC-7  | A note with pitch 60 (C4) and velocity 80 lasting 2 beats | `serialize(project)` is called | The note maps to `[0, 960, 60, 80]` |
| AC-8  | The serializer module | imported in isolation (no socket, no engine) | It imports without error and is callable |
| AC-9  | A project with two tracks of different bar lengths (2 bars and 3 bars) | `serialize(project)` is called | `result["header"]["loop_duration"]` is computed from the 3-bar track (the longest) |
| AC-10 | A project where all tracks are empty | `serialize(project)` is called | `result["header"]["loop_duration"]` equals `0` |
| AC-11 | A note whose beat duration × 480 is not a whole number (e.g. a triplet `1/3` beat) | `serialize(project)` is called | `duration_ticks` is `round(beats * 480)` (nearest integer, no exception raised) |

---

## Open Questions

*(none — all questions resolved)*

---

## Refinement Log

### Cycle 1 — Confidence: 50%
- Reconciled: none (initial PRD creation)
- Added: Q1 (PPQN resolution), Q2 (loop_duration derivation), Q3 (serializer API shape), Q4 (command key ownership), Q5 (stub domain model contract)

### Cycle 2 — Confidence: 72%
- Reconciled: Q1 → F-10 (fixed 480 PPQN), Q2 → F-5 (time-signature arithmetic for loop_duration), Q3 → F-1 (module-level function), Q4 → F-2 (no command key in serializer output), Q5 → F-14 (dataclass stub model); cross-cutting decisions → F-7 (channels 0-indexed), F-8 (note tuple [start_tick, duration_ticks, pitch, velocity])
- Added: Q6 (how bars count is obtained for loop_duration), Q7 (rounding policy for fractional beat-to-tick conversion)

### Cycle 3 — Confidence: 92%
- Reconciled: Q6 → F-5 updated (max bar count across tracks; empty-project edge case produces loop_duration=0); Q7 → F-12 added (round() to nearest integer)
- Added: AC-9 (multi-track loop_duration uses longest track), AC-10 (empty project gives loop_duration=0), AC-11 (fractional tick rounding)
- All open questions resolved
