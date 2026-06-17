# Epic 2 · Socket Transport Layer — PRD

## Overview

Implement the low-level communication layer between py-propeller and the propeller-engine socket interface. The transport layer is responsible for establishing a connection via Unix domain socket, sending a raw JSON payload, reading and interpreting the engine's acknowledgement or error response, and closing the connection. It is deliberately decoupled from the DSL and domain model so that it can be developed, tested, and evolved independently.

**Confidence Level:** 95% — All five open questions fully reconciled. No open ambiguities remain; every requirement, AC, and NFR is specific and individually testable.

---

## User Journeys

### UJ-1 · Send a command and receive acknowledgement

A developer (or the integration layer in Epic 5) assembles a JSON string and passes it to the transport. The transport opens a connection to the engine socket, sends the payload as a newline-terminated string, waits for a single response, then closes the connection. On a `"status":"ok"` response the call returns `None`. This is the happy-path flow for every engine command.

### UJ-2 · Handle an error response from the engine

The transport sends a valid JSON payload but the engine responds with `"status":"error"` and an error code (e.g., `validation_error`, `no_project`). The transport surfaces this to the caller as a `PropellerResponseError` that carries the code as a `.code` attribute, rather than swallowing it or raising a raw string.

### UJ-3 · Handle a connection failure

The developer runs their script but the propeller-engine daemon is not running. The transport attempts to connect and fails. Instead of propagating a raw `OSError` or opaque socket exception, it raises a `PropellerConnectionError` that callers can catch by stable type, with the original OS exception accessible via `.__cause__` and the configured socket path in the message.

---

## Functional Requirements

| ID  | Requirement |
|-----|-------------|
| F-1 | The transport connects to the propeller-engine via a Unix domain socket at a configurable path. |
| F-2 | The socket path is read from the `PROPELLER_SOCK` environment variable **at module import time**, defaulting to `/tmp/propeller.sock` when the variable is not set. The resolved path is stored as the module-level constant `DEFAULT_SOCKET_PATH`. |
| F-3 | A raw JSON string is sent over the connection, terminated with a newline (`\n`) as required by the engine protocol. |
| F-4 | The transport reads the response by consuming the socket until the engine closes the connection (EOF), then parses the accumulated bytes as JSON. |
| F-5 | The transport distinguishes `"status":"ok"` responses from `"status":"error"` responses. |
| F-6 | On an error response, the value of the `"code"` field is surfaced to the caller as `PropellerResponseError.code`. |
| F-7 | The connection is closed after each send/receive cycle; each command uses its own connection (matching the engine's one-command-per-connection contract). |
| F-8 | The transport module has no imports from propeller DSL or domain model modules. |
| F-9 | Connection failures (socket not found, connection refused, timeout) raise `PropellerConnectionError`, wrapping the original OS exception as `__cause__`. |
| F-10 | `PropellerClient` supports the context manager protocol (`__enter__` / `__exit__`) so it can be used in a `with` statement. |
| F-11 | `PropellerClient.send()` returns `None` on a successful `"status":"ok"` response. |
| F-12 | `PropellerClient()` takes **no constructor arguments**. The socket path used is always `DEFAULT_SOCKET_PATH` (the value resolved from the environment at import time). |
| F-13 | `PropellerClient.query()` accepts a raw JSON string, sends it to the engine using the same per-command connection lifecycle as `send()`, and returns the full parsed response dict on a `"status":"ok"` response. On `"status":"error"`, it raises `PropellerResponseError`. On connection failure, it raises `PropellerConnectionError`. |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | The transport has zero coupling to the DSL or domain model: import analysis must find no propeller DSL or composition symbols. |
| NF-2 | The public interface contract (connection lifecycle: open → send → receive → close) is expressed as a Protocol or abstract base class so it can be mocked in tests without a live engine. |
| NF-3 | The transport must not leave open socket connections on exception paths — all cleanup must occur in `finally` blocks or context managers. |
| NF-4 | The implementation uses only synchronous (blocking) stdlib socket I/O. No `asyncio`. |
| NF-5 | `PropellerError` is the library-wide base exception class. `PropellerConnectionError` and `PropellerResponseError` are direct subclasses of `PropellerError` and chain the original exception via `__cause__`. |
| NF-6 | Test isolation for socket path is achieved by patching `DEFAULT_SOCKET_PATH` at the module level (e.g. via `monkeypatch.setattr`) or by setting `PROPELLER_SOCK` before the module is imported in test fixtures — not via constructor arguments. |

---

## Acceptance Criteria

| ID    | Given | When | Then |
|-------|-------|------|------|
| AC-1  | The engine socket is available at the configured path | A `PropellerClient` calls `.send()` with a valid JSON payload | The connection is established and the payload is sent without error |
| AC-2  | An open connection to the engine | A JSON payload is sent | The engine receives it as a newline-terminated UTF-8 string |
| AC-3  | The engine returns `{"status": "ok", ...}` | The transport reads the response | `.send()` returns `None` with no exception raised |
| AC-4  | The engine returns `{"status": "error", "code": "validation_error"}` | The transport reads the response | `PropellerResponseError` is raised with `.code == "validation_error"` |
| AC-5  | The engine socket is unavailable | A `PropellerClient` calls `.send()` | `PropellerConnectionError` is raised (not a bare `OSError`) with the configured socket path in the message |
| AC-6  | A send/receive cycle completes (success or error response) | The cycle ends | The socket connection is closed |
| AC-7  | A send/receive cycle fails with a socket-level exception | The exception propagates | The socket connection is still closed (no leak) |
| AC-8  | The transport module source is inspected | Its imports are listed | No propeller DSL or domain model symbol appears |
| AC-9  | `PROPELLER_SOCK=/run/propeller.sock` is set in the environment **before the module is imported** | A `PropellerClient` is instantiated | The client connects to `/run/propeller.sock` |
| AC-10 | `PROPELLER_SOCK` is not set | A `PropellerClient` is instantiated | The client connects to `/tmp/propeller.sock` |
| AC-11 | A `PropellerClient` is used as a context manager | The `with` block exits (normally or via exception) | The client exits cleanly with no unclosed resources |
| AC-12 | `PropellerConnectionError` is raised | The caller inspects `.__cause__` | The original `OSError` is accessible |
| AC-13 | `PropellerClient()` is called | The constructor signature is inspected | It accepts no arguments (beyond `self`) |
| AC-14 | The engine returns `{"status":"ok","project_present":true}` | `query()` reads the response | The full dict `{"status":"ok","project_present":true}` is returned to the caller |
| AC-15 | The engine returns `{"status":"error","code":"some_error"}` | `query()` reads the response | `PropellerResponseError` is raised with `.code == "some_error"` |
| AC-16 | The engine socket is unavailable | `query()` is called | `PropellerConnectionError` is raised |

---

## Open Questions

_All questions resolved. No open questions remain._

---

## Refinement Log

### Cycle 1 — Confidence: 45%
- Reconciled: none (PRD created from scratch)
- Added: Q-1 (socket addressing model conflict), Q-2 (public API shape), Q-3 (error type hierarchy), Q-4 (sync vs async)

### Cycle 2 — Confidence: 45%
- Reconciled: none (answers collected, not yet reconciled)
- Added: answers recorded in Q-1 through Q-4

### Cycle 3 — Confidence: 85%
- Reconciled: Q-1 → F-1 (Unix socket), F-2 (PROPELLER_SOCK env var + default), F-4 (read until EOF), AC-9 (env var respected), AC-10 (default path); Q-2 → F-10 (context manager), F-11 (send returns None), AC-3 (tightened to "returns None"), AC-11 (context manager exit); Q-3 → NF-5 (PropellerError hierarchy + __cause__ chaining), F-9 (updated to mention __cause__), AC-4 (tightened to .code attribute), AC-12 (__cause__ accessible); Q-4 → NF-4 (synchronous blocking, no asyncio)
- Added: Q-5 (constructor socket path argument vs env-var precedence)

### Cycle 4 — Confidence: 95%
- Reconciled: Q-5 → F-2 (env-var resolved at module import time, stored as DEFAULT_SOCKET_PATH), F-12 (PropellerClient takes no constructor arguments), NF-6 (test isolation via monkeypatching DEFAULT_SOCKET_PATH or env-var before import), AC-9 (tightened: env var must be set before module import), AC-13 (new: constructor accepts no arguments)
- All open questions resolved. No further questions needed.

### Cycle 5 — Confidence: 95%
- Reconciled: non-blocking mode in Epic 5 requires reading the `status` response body — F-13 (new `query()` method returning parsed response dict) and AC-14/AC-15/AC-16 added; `send()` contract unchanged (still returns `None`)
