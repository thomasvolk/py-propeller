# 2 · Socket Transport Layer — Technical Specification

## Overview

Epic 2 implements the low-level communication layer between py-propeller and the
propeller-engine. It introduces `propeller/transport.py` with a `PropellerClient` that opens a
Unix domain socket, sends a newline-terminated JSON payload, reads the engine's response until
EOF, and raises typed exceptions for error responses and connection failures. Two new exception
classes are added to the existing `propeller/errors.py`. The transport has zero coupling to the
DSL or domain model and uses only synchronous stdlib socket I/O.

**Confidence Level:** 92% — All questions and decisions resolved. Architecture, data model, and
task table fully cover every F-x and AC-x. Residual 8%: exact mock fixture wiring for
`recv` side-effects is implementation-level detail left to the implementor.

---

## Architecture Overview

Two modules are touched in this epic:

- `propeller/errors.py` — extended (not replaced) with `PropellerConnectionError` and
  `PropellerResponseError`, both direct subclasses of the existing `PropellerError`.
- `propeller/transport.py` — new module; contains `DEFAULT_SOCKET_PATH`, `TransportProtocol`,
  and `PropellerClient`. Has no imports from `propeller.notes` or any other DSL module (F-8,
  NF-1).

**Socket path resolution** happens at module import time:

```python
DEFAULT_SOCKET_PATH = os.environ.get('PROPELLER_SOCK', '/tmp/propeller.sock')
```

This value is never re-read at call time; test isolation is achieved by patching
`propeller.transport.DEFAULT_SOCKET_PATH` via `monkeypatch.setattr`, or by setting
`PROPELLER_SOCK` before the module is first imported (NF-6).

**Per-command connection lifecycle** (inside `PropellerClient.send()`):

```
open AF_UNIX socket to DEFAULT_SOCKET_PATH
  → send (payload + "\n").encode("utf-8")
  → recv loop until empty bytes (EOF from engine)
  → json.loads(accumulated bytes)
  → if status "ok"  → return None
  → if status "error" → raise PropellerResponseError(code=response["code"])
close socket (guaranteed by `with socket.socket(...) as sock:` context manager)
```

`PropellerClient` holds no persistent connection. Each `.send()` call owns the full
open → send → receive → close lifecycle (F-7). The context manager protocol on
`PropellerClient` itself (`__enter__` / `__exit__`) is therefore a no-op wrapper — it exists
to satisfy the interface contract (F-10) and to let callers use `with PropellerClient() as c:`.

Connection failures (any `OSError` from `sock.connect`) are caught and re-raised as
`PropellerConnectionError(f"Cannot connect to {DEFAULT_SOCKET_PATH}: {e}") from e` (F-9, NF-5).

`TransportProtocol` is a `@runtime_checkable` `typing.Protocol` so higher-level epics
(e.g. Epic 5) can depend on an abstraction and satisfy it structurally — test doubles need no
explicit inheritance (NF-2, D-1).

**Test socket strategy:** unit tests patch `socket.socket` with `unittest.mock.patch`, configure
the resulting mock as a context manager (`mock.__enter__.return_value = mock_conn`), and set
`mock_conn.recv.side_effect` to return response bytes followed by `b""` to simulate EOF (Q-1).

---

## Components

### `propeller/errors.py` (extended)

Adds two new exception classes. Existing `PropellerError` and `PropellerValidationError` from
Epic 1 are unchanged.

- `PropellerConnectionError(PropellerError)` — raised when a socket connection cannot be
  established. The original `OSError` is chained via `__cause__` (NF-5).
- `PropellerResponseError(PropellerError)` — raised when the engine responds with
  `"status":"error"`. Carries a `.code: str` attribute holding the value of the engine's
  `"code"` field (F-6).

### `propeller/transport.py`

**`DEFAULT_SOCKET_PATH: str`** — module-level constant, resolved from `PROPELLER_SOCK`
environment variable at import time; falls back to `/tmp/propeller.sock` (F-2).

**`TransportProtocol`** — `@runtime_checkable` `typing.Protocol` (D-1) exposing:
- `send(self, payload: str) -> None`
- `__enter__(self) -> TransportProtocol`
- `__exit__(self, *args) -> None`

`PropellerClient` satisfies `TransportProtocol` structurally; no explicit inheritance needed.
`isinstance(client, TransportProtocol)` returns `True` at runtime.

**`PropellerClient`** — concrete implementation of `TransportProtocol`:
- `__init__(self)` — no arguments (F-12, AC-13).
- `send(self, payload: str) -> None` — full connection lifecycle per call; returns `None` on
  success; raises `PropellerResponseError` on engine error; raises `PropellerConnectionError` on
  OS-level failure (F-3, F-4, F-5, F-6, F-7, F-9, F-11).
- `__enter__ / __exit__` — no-op wrapper; `__exit__` does not suppress exceptions (F-10).

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `PropellerConnectionError` | — (inherits `args` from `Exception`) | Subclass of `PropellerError`. Original `OSError` accessible via `.__cause__`. |
| `PropellerResponseError` | `code: str` | Subclass of `PropellerError`. `code` set from engine's `"code"` field. |
| `DEFAULT_SOCKET_PATH` | `str` | Module-level constant in `transport.py`. Resolved once at import time. |
| `TransportProtocol` | — | `@runtime_checkable` `typing.Protocol` with `send`, `__enter__`, `__exit__`. |
| `PropellerClient` | — | Stateless; no instance fields. Satisfies `TransportProtocol` structurally. |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID   | Task | Type | PRD ref | Depends on |
|------|------|------|---------|------------|
| T-1  | Test: `PropellerConnectionError` and `PropellerResponseError` importable from `propeller.errors`; both subclass `PropellerError`; `PropellerResponseError(code="x").code == "x"` | test | F-6, F-9, NF-5 | — |
| I-1  | Add `PropellerConnectionError(PropellerError)` and `PropellerResponseError(PropellerError)` with `code: str` constructor arg to `propeller/errors.py` | impl | F-6, F-9, NF-5 | T-1 |
| T-2  | Test: importing `propeller.transport` with `PROPELLER_SOCK` unset yields `DEFAULT_SOCKET_PATH == "/tmp/propeller.sock"` | test | F-2, AC-10 | — |
| T-3  | Test: `DEFAULT_SOCKET_PATH` equals the value of `PROPELLER_SOCK` when the env var is set before the module is imported | test | F-2, AC-9 | — |
| I-2  | Create `propeller/transport.py`; set `DEFAULT_SOCKET_PATH = os.environ.get('PROPELLER_SOCK', '/tmp/propeller.sock')` | impl | F-2 | T-2, T-3 |
| T-4  | Test: `TransportProtocol` is importable from `propeller.transport`; `isinstance(PropellerClient(), TransportProtocol)` is `True`; protocol specifies `send(str) -> None` and context manager methods | test | NF-2 | I-2 |
| I-3  | Define `@runtime_checkable` `typing.Protocol` named `TransportProtocol` in `propeller/transport.py` with `send(self, payload: str) -> None`, `__enter__`, `__exit__` | impl | NF-2 | T-4 |
| T-5  | Test: `PropellerClient()` instantiates with no arguments; passing any argument raises `TypeError` | test | F-12, AC-13 | I-2 |
| T-6  | Test: `PropellerClient` used as context manager — `__enter__` returns the client instance; `__exit__` completes without error on normal and exception exit | test | F-10, AC-11 | I-2 |
| I-4  | Implement `PropellerClient` with no-arg `__init__`; `__enter__` returns `self`; `__exit__` is a no-op | impl | F-10, F-12 | T-5, T-6, I-3 |
| T-7  | Test: via `mock.patch('socket.socket')`, verify `send(payload)` opens `AF_UNIX / SOCK_STREAM` socket to `DEFAULT_SOCKET_PATH` and calls `sendall` with `(payload + "\n").encode("utf-8")` | test | F-1, F-3, AC-1, AC-2 | I-4 |
| T-8  | Test: via `mock.patch('socket.socket')` with `recv.side_effect = [b'{"status": "ok"}', b""]`, verify `send(payload)` returns `None` | test | F-4, F-5, F-11, AC-3 | I-4 |
| I-5  | Implement `PropellerClient.send()`: open `socket.socket(AF_UNIX, SOCK_STREAM)` to `DEFAULT_SOCKET_PATH`, send payload as UTF-8 with newline, `recv` until EOF, `json.loads`, return `None` on `"status":"ok"` | impl | F-1, F-3, F-4, F-5, F-7, F-11 | T-7, T-8 |
| T-9  | Test: via `mock.patch('socket.socket')` with `recv.side_effect = [b'{"status": "error", "code": "validation_error"}', b""]`, verify `send()` raises `PropellerResponseError` with `.code == "validation_error"` | test | F-5, F-6, AC-4 | I-5 |
| I-6  | Add error-response branch: if `response["status"] == "error"`, raise `PropellerResponseError(code=response["code"])` | impl | F-5, F-6 | T-9 |
| T-10 | Test: via `mock.patch('socket.socket')` where `connect` raises `OSError`, verify `send()` raises `PropellerConnectionError` (not bare `OSError`); message contains `DEFAULT_SOCKET_PATH`; `.__cause__` is the original `OSError` | test | F-9, AC-5, AC-12 | I-5 |
| I-7  | Wrap `sock.connect()` in `try/except OSError`; re-raise as `PropellerConnectionError(f"Cannot connect to {DEFAULT_SOCKET_PATH}: {e}") from e` | impl | F-9 | T-10 |
| T-11 | Test: via `mock.patch('socket.socket')`, verify the mock socket context manager is entered and exited after a successful cycle, after a `PropellerResponseError`, and when `connect` raises — confirming no fd leak on any path | test | F-7, NF-3, AC-6, AC-7 | I-5, I-6, I-7 |
| I-8  | Ensure `send()` wraps the entire socket lifecycle in `with socket.socket(AF_UNIX, SOCK_STREAM) as sock:` so the OS closes the fd on every code path | impl | NF-3 | T-11 |
| T-12 | Test: static inspection of `propeller/transport.py` imports — no symbol from `propeller.notes` or any other propeller DSL module appears | test | F-8, NF-1, AC-8 | I-2 |

---

## Open Questions

None — all questions resolved.

---

## Open Decisions

None — all decisions resolved.

---

## Revision Log

### Cycle 1 — Confidence: 65%
- Reconciled: nothing (spec created fresh from PRD)
- Added: Q-1 (socket test strategy), D-1 (Protocol vs ABC interface)

### Cycle 2 — Confidence: 65%
- Reconciled: nothing (Q-1 unanswered, D-1 unchecked)
- Added: nothing (existing Q-1 and D-1 cover all open ambiguities)

### Cycle 3 — Confidence: 92%
- Reconciled: Q-1 → A (mock.patch strategy); Architecture Overview updated with mock pattern; T-7, T-8, T-9, T-10, T-11 updated with explicit patch/side-effect wording
- Reconciled: D-1 → A (typing.Protocol + @runtime_checkable); Architecture Overview, Components, Data Model, I-3, T-4 updated to reflect structural Protocol
- No open questions or decisions remain
