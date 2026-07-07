# EP-1 · Pitch Bend DSL Element — PRD

## Overview

A composer can write `PB(value)` anywhere within a track's note list to declare a pitch-bend event. The argument is a float in the range -1.0 to 1.0, where -1.0 is maximum downward bend, 0.0 is no bend, and 1.0 is maximum upward bend. Using `PB` as a bare name (without calling it) is equivalent to `PB(0.0)`. A pitch-bend element carries no duration of its own; it is positionally associated with the note that immediately follows it in the sequence.

**Confidence Level:** 92% — all requirements from the roadmap are covered and both open questions are resolved; minor residual ambiguity around whether the trailing-PB (no following note) is silently ignored or causes a warning.

---

## User Journeys

### UJ-1 · Composer adds a pitch bend before a note

A composer wants to hear a note played with an upward half-bend. They write `PB(0.5)` in the note list immediately before the target note. The DSL accepts the sequence without error and the pitch-bend is associated with that note.

### UJ-2 · Composer resets pitch to center using the bare constant

A composer wants to reset pitch bend to center before a note without specifying a value. They write the bare name `PB` (without calling it). The DSL accepts this and treats it identically to `PB(0.0)`.

### UJ-3 · Composer places a pitch bend at the end of a note list

A composer writes a `PB` element after the last note in a track's list. No following note exists. The DSL accepts the sequence without error.

### UJ-4 · Composer provides an out-of-range value

A composer accidentally writes `PB(1.5)`. The DSL rejects the construction immediately and raises a DSL-specific exception with a message that clearly identifies the invalid value and the accepted range.

### UJ-5 · Composer accidentally places two consecutive `PB` elements before one note

A composer writes `PB(0.5), PB(-0.3), D4(100)` in a note list. The DSL raises a DSL-specific exception identifying that consecutive pitch-bend elements are not permitted before a single note.

---

## Functional Requirements

| ID  | Requirement |
| --- | ----------- |
| F-1 | The DSL exposes a `PB` element that can be called with a single float argument in the range -1.0 to 1.0 (inclusive). |
| F-2 | `PB` used as a bare name (without being called) is accepted and is semantically equivalent to `PB(0.0)`. |
| F-3 | A `PB` element has no duration; it does not advance the tick position of subsequent elements. |
| F-4 | A `PB` element is positionally associated with the note that immediately follows it in the note list. |
| F-5 | Float values outside -1.0 to 1.0 are rejected at construction time with a descriptive error. |
| F-6 | A `PB` element placed at the end of a note list (with no following note) is accepted without error. |
| F-7 | Multiple consecutive `PB` elements appearing before a single note raise a DSL-specific error at construction time. |
| F-8 | A track containing no `PB` elements behaves identically to current DSL behavior. |

---

## Non-Functional Requirements

| ID   | Requirement |
| ---- | ----------- |
| NF-1 | The error raised for an out-of-range value must include the invalid value and the accepted range (-1.0 to 1.0) in its message. |
| NF-2 | All errors raised for pitch-bend violations (out-of-range value, consecutive `PB` elements) must be instances of a custom DSL-specific exception type, distinct from built-in Python exceptions. |

---

## Acceptance Criteria

| ID   | Given | When | Then |
| ---- | ----- | ---- | ---- |
| AC-1 | A note list containing `PB(0.5)` followed by a note | The DSL constructs the track | No error is raised |
| AC-2 | A note list containing bare `PB` followed by a note | The DSL constructs the track | No error is raised, and `PB` behaves identically to `PB(0.0)` |
| AC-3 | A note list containing `PB(1.5)` | The DSL constructs the track | A DSL-specific exception is raised that names the invalid value and the accepted range |
| AC-4 | A note list whose final element is `PB(0.3)` with no following note | The DSL constructs the track | No error is raised |
| AC-5 | A note list containing `PB(0.5)` then `PB(-0.3)` before a single note | The DSL constructs the track | A DSL-specific exception is raised identifying the consecutive pitch-bend elements |
| AC-6 | A track with no `PB` elements | The DSL constructs and represents the track | The result is identical to current DSL behavior |
| AC-7 | A note list containing `PB(1.5)` | The DSL constructs the track | The raised exception is an instance of the DSL-specific exception type (not a plain `ValueError` or `TypeError`) |
| AC-8 | A note list containing `PB(0.5)` then `PB(-0.3)` before a single note | The DSL constructs the track | The raised exception is an instance of the DSL-specific exception type |

---

## Open Questions

*(none)*

---

## Refinement Log

### Cycle 1 — Confidence: 70%
- Reconciled: nothing (first cycle, PRD created from roadmap)
- Added: Q1 (multiple consecutive PB semantics), Q2 (error type for out-of-range)

### Cycle 2 — Confidence: 92%
- Reconciled: Q1 → F-7 updated (consecutive PBs raise error), AC-5 updated (expects error), UJ-5 added; Q2 → NF-2 added (custom DSL-specific exception type), AC-7 and AC-8 added
- Added: nothing (confidence ≥ 90%)
