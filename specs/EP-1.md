# EP-1 · Sync Mode — PRD

## Overview

When the `-s sync` flag is passed to `play()`, py-propeller sends project data to the engine but suppresses all loop lifecycle commands (`loop-start` and `loop-stop`). This lets an external clock source (e.g. a DAW or hardware sequencer) own the transport while py-propeller handles only project delivery.

**Confidence Level:** 95% — all requirements are specified and testable; no open ambiguities remain.

---

## User Journeys

### UJ-1 · Push a project to a synced engine

A user has an external clock source driving the engine. They call `play(project)` with `-s sync`. py-propeller sends `create-project` to the engine and exits immediately. No `loop-start` or `loop-stop` message is ever sent. The external source retains full control of transport start and stop.

---

## Functional Requirements

| ID  | Requirement |
| --- | ----------- |
| F-1 | `-s` accepts `sync` as a valid value alongside the existing `inactive` and `active` values. |
| F-2 | When `-s sync` is set, `{"command": "loop-start"}` is never sent to the socket. |
| F-3 | When `-s sync` is set, `{"command": "loop-stop"}` is never sent to the socket. |
| F-4 | The behaviour of `-s inactive`, `-s active`, `-n`, and the no-flag default is unchanged. |
| F-5 | When `-s sync` is set, py-propeller sends `{"command": "create-project", ...}` with the serialized project payload to the socket. |
| F-6 | When `-s sync` is set, the process exits cleanly immediately after the `create-project` command is delivered, without blocking. |

---

## Non-Functional Requirements

| ID   | Requirement |
| ---- | ----------- |
| NF-1 | Passing `-s sync` must not raise an unhandled exception or produce a non-zero exit for a well-formed project. |

---

## Acceptance Criteria

| ID   | Given | When | Then |
| ---- | ----- | ---- | ---- |
| AC-1 | py-propeller is invoked with `-s sync` and a valid project | `play(project)` runs | No `loop-start` command is sent to the socket at any point |
| AC-2 | py-propeller is invoked with `-s sync` and a valid project | `play(project)` runs | No `loop-stop` command is sent to the socket at any point |
| AC-3 | py-propeller is invoked without `-s sync` | `play(project)` runs | loop-start and loop-stop behaviour is unchanged |
| AC-4 | py-propeller is invoked with `-s sync` | `play(project)` runs | The process exits cleanly with no unhandled exception |
| AC-5 | py-propeller is invoked with `-s sync` and a valid project | `play(project)` runs | A `create-project` command with the serialized project payload is sent to the socket |
| AC-6 | py-propeller is invoked with `-s sync` and a valid project | `play(project)` runs | The process exits immediately after the `create-project` command is delivered, without blocking |

---

## Open Questions

_None — all questions resolved._

---

## Refinement Log

### Cycle 1 — Confidence: 60%
- Reconciled: nothing (first cycle, PRD created from roadmap)
- Added: Q1 (project delivery behaviour), Q2 (process lifetime)

### Cycle 2 — Confidence: 95%
- Reconciled: Q1 → F-5, AC-5 (always sends create-project); Q2 → F-6, AC-6 (exits immediately after delivery)
- Added: nothing — PRD is complete
