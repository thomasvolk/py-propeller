# Epic 6 · Validation & Error Feedback — PRD

## Overview

Epic 6 adds meaningful validation to the py-propeller DSL so that users receive
clear, actionable error messages as early as possible — before any network
communication with the propeller-engine occurs. Validation covers three layers:
note primitives (pitch, duration, velocity), composition objects (`track()` and
`project()`), and the connection lifecycle (socket failures translated into
human-readable diagnostics).

**Confidence Level:** 95% — All questions resolved. Every requirement is concrete and individually testable; the exception hierarchy is fully defined; no open ambiguities remain.

---

## User Journeys

### UJ-1 · Invalid note value caught at the point of authoring

A musician writes a DSL script and accidentally constructs a note with an
out-of-range velocity (e.g. `C4(200)`). When they run the script, Python raises a
`PropellerValidationError` immediately — before any serialization or network
activity — with a clear message identifying the offending value and field.

### UJ-2 · Invalid track or project structure caught before playback

A developer calls `track(channel=17, ...)` (MIDI channel out of range for
1-indexed 1–16). On construction, a `PropellerValidationError` is raised with a
message identifying the field and the offending value before any socket is opened.

### UJ-3 · Connection failure produces an actionable diagnostic

A musician runs `python my_project.py` but the propeller-engine is not running.
Instead of a raw `ConnectionRefusedError`, they see a `PropellerConnectionError`
with the socket path and a suggestion to verify the engine is running.

---

## Functional Requirements

| ID  | Requirement |
|-----|-------------|
| F-1 | The `*` duration operator validates its argument at the point of application and raises `PropellerValidationError` if the resulting duration would be non-positive. Operator-time error messages do NOT include note position context. |
| F-2 | Duration (`* beats`) must be a positive number (> 0); non-positive or non-numeric values raise `PropellerValidationError`. |
| F-3 | When `C4(velocity)` is called with a velocity outside [0, 127], `PropellerValidationError` is raised immediately with a message naming the field (`velocity`) and the offending value. |
| F-4 | `track()` validates at construction time: `name` is a non-empty string; `channel` is an integer in the range 1–16 (1-indexed MIDI channel); `instrument` is an integer 0–127. |
| F-5 | `project()` validates at construction time: `bpm` is a positive number; `bars` is a positive integer; `time_signature` is a two-element tuple of positive integers. |
| F-6 | Validation errors raised by `track()` and `project()` occur at construction time — before `.play()` opens any socket connection. |
| F-7 | Socket connection failures (refused, timeout, unreachable) are caught inside `.play()` and re-raised as `PropellerConnectionError` with a message that includes the socket path and a suggestion to verify the engine is running. |
| F-8 | Raw low-level exceptions (`socket.error`, `OSError`, `ConnectionRefusedError`, etc.) must not propagate to the user unhandled; they may appear only as the `__cause__` of a `PropellerConnectionError`. |
| F-9 | When `track()` iterates its `notes` list during construction and encounters a note with an invalid value, the error message must include the note's position within the flat `notes` list using a 1-based index (e.g. `"Invalid velocity at position 3: value 150 exceeds maximum 127"`). There is no bar-index context since bar grouping within tracks has been removed from the DSL. |
| F-10 | The library defines `PropellerError` as its base exception class. `PropellerValidationError` (DSL/structural errors) and `PropellerConnectionError` (transport errors) are subclasses, allowing callers to catch all library errors with a single `except PropellerError` clause. `PropellerResponseError` is out of scope for Epic 6. |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | Validation overhead must be negligible for typical projects (tens of tracks, hundreds of notes); no measurable delay before playback starts. |
| NF-2 | `PropellerError`, `PropellerValidationError`, and `PropellerConnectionError` must be importable from `propeller` (or a documented sub-module) so callers can catch them by type. `PropellerResponseError` is not defined in Epic 6. |
| NF-3 | Error messages must be written in plain English, addressed to a musician/DSL author, not to a Python developer debugging internals. |

---

## Acceptance Criteria

| ID    | Given | When | Then |
|-------|-------|------|------|
| AC-1  | A note constructor is called with a velocity outside [0, 127] | `C4(200)` or `C4(-5)` is evaluated | `PropellerValidationError` is raised immediately with a message naming the field `velocity` and the offending value |
| AC-2  | A note modifier (`*`) would produce a duration ≤ 0 | The modifier expression is evaluated | `PropellerValidationError` is raised with a message naming the note, the field (`duration`), and the requirement that it must be positive; no position context is included |
| AC-3  | `track()` is called with `channel` outside 1–16 | `track()` is called | `PropellerValidationError` is raised naming the field `channel` and the offending value |
| AC-4  | `track()` is called with `instrument` outside 0–127 | `track()` is called | `PropellerValidationError` is raised naming the field `instrument` and the offending value |
| AC-5  | `track()` is called with an empty `name` string | `track()` is called | `PropellerValidationError` is raised naming the field `name` |
| AC-6  | `project()` is called with `bpm` ≤ 0 | `project()` is called | `PropellerValidationError` is raised naming the field `bpm` |
| AC-7  | `project()` is called with `bars` ≤ 0 | `project()` is called | `PropellerValidationError` is raised naming the field `bars` |
| AC-8  | `project()` is called with a `time_signature` that is not a two-element tuple of positive integers | `project()` is called | `PropellerValidationError` is raised naming the field `time_signature` |
| AC-9  | A valid DSL project is built but the engine is not reachable | `.play()` is called | `PropellerConnectionError` is raised with a message containing the socket path and an actionable suggestion; the raw socket exception is accessible as `__cause__` |
| AC-10 | Any validation error is raised by `track()` or `project()` | `.play()` is subsequently not called | No socket connection is ever attempted |
| AC-11 | `track()` iterates its `notes` list and encounters a note with an out-of-range value | `track()` is called | `PropellerValidationError` is raised and the message includes the note's 1-based position in the flat `notes` list (e.g. "position 3") — no bar index is included |
| AC-12 | `PropellerValidationError` is raised | The caller uses `except PropellerError` | The exception is caught, confirming `PropellerValidationError` is a subclass of `PropellerError` |
| AC-13 | `PropellerConnectionError` is raised | The caller uses `except PropellerError` | The exception is caught, confirming `PropellerConnectionError` is a subclass of `PropellerError` |

---

## Refinement Log

### Cycle 1 — Confidence: 60%
- Reconciled: none (PRD created fresh from roadmap)
- Added: Q1 (validation timing), Q2 (exception hierarchy), Q3 (MIDI channel convention), Q4 (note-position context in error messages)

### Cycle 2 — Confidence: 80%
- Reconciled: Q1 → F-4, F-5, F-6 (construction-time validation); Q2 → F-10, NF-2, AC-11, AC-12 (PropellerError hierarchy); Q3 → F-4, AC-3 (1-indexed channel range 1–16); Q4 → F-9, AC-10 (bar index + note position in track()-level error messages)
- Added: Q5 (which layer produces bar/position messages), Q6 (0-based vs 1-based index in messages), Q7 (PropellerResponseError scope)

### Cycle 3 — Confidence: 95%
- Reconciled Q5 → F-1 (operator-time guards raise without bar/position context), F-9 (track() is the sole source of bar/position-enriched messages), AC-1, AC-2 (no position context in operator errors), AC-10 (track() provides bar/position context)
- Reconciled Q6 → F-9 (1-based indices), AC-10 (1-based indices, example updated)
- Reconciled Q7 → F-10 (PropellerResponseError removed from Epic 6 scope), NF-2 (PropellerResponseError removed)
- Fixed: F-4 and F-7 updated to reference socket path; parameter name updated from `notes` to `bars` to match Epic 3
- All open questions resolved

### Cycle 4 — Confidence: 75%
- Context: briefing.md updated to drop bars concept; `track()` takes flat `notes=[]`.
- F-9 updated: bar-index removed from error messages; position in flat notes list (1-based) only.
- AC-10 updated: "position 3" replaces "bar 2, position 3".
- F-1 and F-3 flagged as pending Epic 1 Q5; AC-1 flagged pending Q5.
- Added: Q8 (constructor-arg velocity validation, blocked on Epic 1 Q5)

### Cycle 5 — Confidence: 82%
- Reconciled: Epic 1 Q5-A → `+`/`-` velocity operators removed from the language.
  - F-1 updated: only `*` duration operator remains; `+`/`-` references removed.
  - F-3 updated: replaced `+`/`-` velocity range check with constructor-arg velocity placeholder (pending Q6).
  - AC-1 updated: replaced `+`/`-` AC with constructor-arg out-of-range placeholder (pending Q6).
- Reconciled: Epic 3 Q7-C → `bars=N` restored on `project()`.
  - F-5 updated: `bars` positive integer added to `project()` validation.
  - AC-7 added: `project(bars=0)` raises `PropellerValidationError`.
  - AC-8 (old: time_signature) renumbered to AC-8; new bars AC inserted as AC-7.
  - All subsequent ACs renumbered.
- Q8 updated: unblocked from Epic 1 Q5 (now answered); still blocked on Epic 1 Q6.

### Cycle 6 — Confidence: 95%
- Reconciled: Q8-A → F-3 (raise `PropellerValidationError` immediately on out-of-range velocity), AC-1 (concrete Given/When/Then; clamping option removed)
- Removed: Q8 (fully resolved); UJ-1 pending note removed
- No open questions remain; PRD is complete
