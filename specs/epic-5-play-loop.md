# Epic 5 · Play Loop & Script Lifecycle — PRD

## Overview

Epic 5 wires together the DSL (Epic 3), JSON serialization (Epic 4), and socket transport (Epic 2) into the `.play()` method on the project object. When a musician runs their script, `.play()` sends a `create-project` command followed by a `loop-start` command to the propeller-engine over its Unix domain socket, then blocks the process so the script stays alive. Pressing Ctrl+C triggers a clean shutdown: the loop is stopped on the engine and the process exits with no error output. A dry-run mode (`-n` CLI flag) skips the socket entirely, prints the JSON payloads to stdout, and returns immediately.

**Confidence Level:** 95% — All open questions resolved. Requirements are specific and testable, shutdown error-suppression behaviour and dry-run behaviour are fully specified, no ambiguities remain.

---

## User Journeys

### UJ-1 · Run a musical script

A musician writes a Python script using the propeller DSL, calls `.play()` at the end, and runs it with `python my_project.py`. The library serializes the project, sends it to the already-running propeller-engine daemon, then starts the loop. Music begins playing immediately. The script stays alive, keeping the terminal session attached so the musician knows it is running.

### UJ-2 · Stop playback cleanly

A musician presses Ctrl+C while the script is blocking. The library sends a `loop-stop` command to the engine (stopping the MIDI loop without killing the daemon), then exits cleanly — no exception traceback, no hung thread, exit code 0.

### UJ-3 · Connect to a non-default socket path

A musician started the engine with a custom socket path (`PROPELLER_SOCK=/run/user/1000/propeller.sock propeller start`). They set the same env var in their shell before running their script. `.play()` picks it up automatically — no code changes needed.

### UJ-4 · Dry-run a script without a running engine

A musician wants to inspect what would be sent to the engine before starting playback. They run `python my_project.py -n`. The library serializes the project and prints each JSON command payload to the console, one per line. The script exits immediately. No engine connection is attempted and no socket path needs to be configured.

---

## Functional Requirements

| ID  | Requirement |
|-----|-------------|
| F-1 | `play()` serializes the project to a valid `create-project` JSON payload (as defined by the propeller-engine JSON socket interface) and sends it to the engine socket. |
| F-2 | `play()` sends a `loop-start` command to the engine immediately after `create-project` receives a successful response. |
| F-3 | After both commands are sent, `play()` blocks the calling process indefinitely, keeping the script alive until interrupted. |
| F-4 | The socket path defaults to `/tmp/propeller.sock` and is overridable via the `PROPELLER_SOCK` environment variable without any code changes. |
| F-5 | Each engine command is sent on its own independent connection (open → send newline-terminated JSON → receive one-line JSON response → close), matching the engine's one-command-per-connection protocol. |
| F-6 | A `KeyboardInterrupt` (Ctrl+C) triggers a `loop-stop` command to the engine, then exits the process cleanly with no error traceback. |
| F-7 | If the engine returns `{"status":"error", ...}` to `create-project`, `PropellerResponseError` is raised immediately with the engine's error message; `loop-start` is not sent. |
| F-8 | The library defines `PropellerError` as the public base exception with two concrete subclasses: `PropellerResponseError` (engine returned an error status) and `PropellerConnectionError` (socket unreachable or connection refused). |
| F-9 | If sending `loop-stop` during Ctrl+C shutdown fails (engine crashed, socket gone), the error is silently suppressed and the process exits with code 0. |
| F-10 | When `-n` is present in `sys.argv`, `.play()` operates in dry-run mode: it serializes the project and prints each JSON command payload (`create-project`, `loop-start`) to stdout, one per line, instead of sending them to the engine. |
| F-11 | In dry-run mode, no socket connection is attempted and `.play()` returns immediately after printing (non-blocking). |
| F-12 | Dry-run mode is detected from `sys.argv` at the point `.play()` is called; it does not require changes to the `project()` or `track()` DSL calls. |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | The idle blocking loop does not busy-wait — it sleeps between polls using `time.sleep()`, consuming negligible CPU. |
| NF-2 | The full shutdown sequence (Ctrl+C received → `loop-stop` sent → process exits) completes in under 2 seconds. |
| NF-3 | The process exits with code 0 on clean Ctrl+C shutdown — an intentional stop is a normal, successful outcome. |
| NF-4 | The implementation is synchronous and blocking only; asyncio is not used. |
| NF-5 | A failed `loop-stop` during shutdown produces no output to stderr and does not affect the exit code. |

---

## Acceptance Criteria

| ID   | Given | When | Then |
|------|-------|------|------|
| AC-1 | A valid project object | `.play()` is called | A `create-project` JSON command is sent to the engine socket and a `{"status":"ok"}` response is received |
| AC-2 | `create-project` succeeds | `.play()` continues | A `loop-start` command is sent immediately after |
| AC-3 | Both commands have been sent successfully | `.play()` is executing | The process blocks and does not exit until interrupted |
| AC-4 | `PROPELLER_SOCK` is not set in the environment | `.play()` is called | The socket path `/tmp/propeller.sock` is used |
| AC-5 | `PROPELLER_SOCK` is set to a custom path | `.play()` is called | That custom path is used instead of the default |
| AC-6 | The script is blocking in `.play()` | Ctrl+C is pressed | A `loop-stop` command is sent to the engine, the process exits with code 0, and no exception traceback is printed |
| AC-7 | The engine returns `{"status":"error", "message":"..."}` to `create-project` | `.play()` processes the response | `PropellerResponseError` is raised with the engine's error message and `loop-start` is never sent |
| AC-8 | The script is blocking in `.play()` and the engine has crashed | Ctrl+C is pressed | The `loop-stop` failure is silently ignored, no traceback is printed, and the process exits with code 0 |
| AC-9 | `-n` is in `sys.argv` | `.play()` is called | A `create-project` JSON line and a `loop-start` JSON line are printed to stdout, no socket is opened, and the call returns immediately |
| AC-10 | `-n` is not in `sys.argv` | `.play()` is called | Behaviour is unchanged from AC-1 through AC-8 (live mode) |

---

## Open Questions

None — all questions resolved.

---

## Refinement Log

### Cycle 1 — Confidence: 62%
- Reconciled: none (initial creation)
- Added: Q1 (Unix socket vs TCP host/port — roadmap discrepancy), Q2 (engine shutdown signal), Q3 (blocking mechanism), Q4 (error response from create-project)
- Note: Engine uses Unix domain socket (`PROPELLER_SOCK`), not TCP. Roadmap AC "host and port" is a factual mismatch with the actual interface; Q1 surfaces this for the user to confirm.

### Cycle 2 — Confidence: 88%
- Reconciled: Q1 → AC-4, AC-5, F-4 confirmed correct (Unix socket / PROPELLER_SOCK; no new entries needed); Q2 → F-6, AC-6 confirmed correct (loop-stop, daemon stays running); Q3 → NF-1 tightened to `time.sleep()`, NF-4 added (sync-only, no asyncio); Q4 → F-7 (PropellerResponseError on create-project error), F-8 (exception hierarchy: PropellerError / PropellerResponseError / PropellerConnectionError), AC-7 (testable error scenario)
- Added: Q5 (loop-stop failure resilience during Ctrl+C shutdown)

### Cycle 3 — Confidence: 95%
- Reconciled: Q5 → F-9 (silent suppression of loop-stop failure, exit 0), NF-5 (no stderr output on shutdown failure), AC-8 (testable crashed-engine shutdown scenario)
- No open questions remain

### Cycle 4 — Confidence: 95%
- Reconciled: dry-run feature added from briefing update — F-10, F-11, F-12, AC-9, AC-10, UJ-4 added; overview updated; no prior requirements changed
