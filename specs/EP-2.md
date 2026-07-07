# EP-2 · Pitch Bend Serialization and Transmission — PRD

## Overview

When a project is played, any pitch-bend elements in a track are included in the JSON payload sent to propeller-engine. Each bend is emitted as a two-element integer array `[tick, value]` inside the track's `pitch-bends` field. The tick is the offset from the start of the loop at which the bend occurs (equal to the tick of the immediately following note). The 14-bit integer value (0–16383) is derived from the DSL float using `round((dsl_float + 1.0) / 2.0 * 16383)`, with 8192 representing no bend. Tracks without pitch-bend elements omit the `pitch-bends` field entirely. The resulting payload is transmitted via socket in the same way as all other track data.

**Confidence Level:** 93% — all roadmap requirements are covered, all questions are resolved, and every AC is unit-testable; minor residual ambiguity around whether a track containing only trailing PBs (and no notes at all) deserves an explicit user journey, though F-8 and AC-8 cover it functionally.

---

## User Journeys

### UJ-1 · Composer plays a project containing pitch bends

A composer has written a track with one or more `PB(value)` elements. They call `p.play()`. The DSL serializes the pitch-bend events into the JSON payload, including a `pitch-bends` array in the track object, and transmits the full payload to propeller-engine via socket. The engine receives the payload and plays the track with the correct pitch modulation.

### UJ-2 · Composer plays a project with no pitch bends

A composer plays a project that contains no `PB` elements. The serialized JSON is identical to current behavior: no `pitch-bends` field is present, and propeller-engine plays the track as before. No regressions occur.

### UJ-3 · Composer uses the full range of pitch-bend values

A composer writes `PB(-1.0)`, `PB(0.0)` (or bare `PB`), and `PB(1.0)` in a track. Each serializes to the correct 14-bit boundary value (0, 8192, and 16383 respectively), demonstrating that the float-to-integer conversion covers the full range.

---

## Functional Requirements

| ID  | Requirement |
| --- | ----------- |
| F-1 | Each `PB` element in a track is serialized as a two-element integer array `[tick, value]` and appended to the track's `pitch-bends` list in tick order. |
| F-2 | The tick of a serialized pitch-bend event equals the tick of the note immediately following that `PB` element in the note list. |
| F-3 | The 14-bit integer value is computed from the DSL float as `int(round((dsl_float + 1.0) / 2.0 * 16383))`, mapping -1.0 → 0, 0.0 → 8192, and 1.0 → 16383. |
| F-4 | A track with no `PB` elements omits the `pitch-bends` field from the JSON output entirely. |
| F-5 | The serialized tick of each pitch-bend event must be strictly less than the loop duration. |
| F-6 | The full project JSON including `pitch-bends` data is transmitted to propeller-engine via the existing socket mechanism without modification to the transmission layer. |
| F-7 | Existing projects that contain no `PB` elements serialize and transmit identically to current behavior. |
| F-8 | A `PB` element at the end of a note list with no following note is silently omitted from the `pitch-bends` output; it produces no entry in the array and raises no error. |

---

## Non-Functional Requirements

| ID   | Requirement |
| ---- | ----------- |
| NF-1 | No performance regression is introduced for tracks or projects that contain no `PB` elements. |
| NF-2 | The serialized `pitch-bends` list is ordered by ascending tick value. |
| NF-3 | Socket transmission (F-6) is verified by unit-testing the serialized JSON structure passed to the socket layer; no live propeller-engine connection is required in the test suite. |

---

## Acceptance Criteria

| ID   | Given | When | Then |
| ---- | ----- | ---- | ---- |
| AC-1 | A track containing `PB(0.5)` immediately before a note | The project is serialized | The `pitch-bends` array contains an entry whose tick equals the tick of that note and whose value is greater than 8192 |
| AC-2 | A track containing `PB(0.0)` and a track containing bare `PB` before a note | Each project is serialized | Both produce a `pitch-bends` entry with value 8192 |
| AC-3 | A track containing `PB(-1.0)` and a track containing `PB(1.0)` | Each project is serialized | `PB(-1.0)` produces value 0 and `PB(1.0)` produces value 16383 |
| AC-4 | A track with pitch-bend events | The project is serialized | Every entry in `pitch-bends` has a tick strictly less than the loop duration |
| AC-5 | A track with no `PB` elements | The project is serialized | The `pitch-bends` field is absent from the track's JSON object |
| AC-6 | A project with pitch-bend events in one or more tracks | `p.play()` is called | The JSON payload passed to the socket layer contains `pitch-bends` in the correct format for each track that has pitch-bend events |
| AC-7 | An existing project that has no `PB` elements | `p.play()` is called | The project plays correctly and the output JSON is unchanged from current behavior |
| AC-8 | A track whose final element is a `PB` with no following note | The project is serialized | No `pitch-bends` entry is produced for that trailing `PB` |

---

## Open Questions

*(none)*

---

## Refinement Log

### Cycle 1 — Confidence: 65%
- Reconciled: nothing (first cycle, PRD created from roadmap)
- Added: Q-1 (trailing PB serialization behavior), Q-2 (empty pitch-bends field presence)

### Cycle 2 — Confidence: 85%
- Reconciled: Q-1 → F-8 (trailing PB silently omitted), AC-8 added; Q-2 → F-4 updated (omit field entirely), AC-5 tightened (field absent, not "or empty list"), UJ-2 updated
- Added: Q-3 (socket transmission test strategy)

### Cycle 3 — Confidence: 93%
- Reconciled: Q-3 → NF-3 (unit test sufficient for socket; no live engine required), AC-6 reworded to be unit-testable (inspects JSON passed to socket layer)
- Added: nothing (confidence ≥ 90%)
