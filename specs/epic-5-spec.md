# 5 · Play Loop & Script Lifecycle — Technical Specification

## Overview

Epic 5 wires together the DSL (`Project`, Epic 3), JSON serialization (`serialize`, Epic 4), and
the socket transport (`PropellerClient`, Epic 2) into a `.play()` method on the `Project` class.
The implementation lives in a new `propeller/player.py` module; `Project.play()` in
`composition.py` delegates to it via a lazy import to avoid circular dependencies. Calling
`.play()` serializes the project, sends `create-project` then `loop-start` to the engine over
the Unix socket, then blocks with `time.sleep()` until Ctrl+C — which triggers `loop-stop` and
a clean `sys.exit(0)`.

**Confidence Level:** 92% — All decisions resolved; architecture, data model, and task table fully
cover every F-x and AC-x. Residual 8%: NF-2 (shutdown < 2 s) has no explicit timing test —
correctness is structural (OSError is raised immediately on a crashed engine) rather than measured.

---

## Architecture Overview

Three files are affected:

- `propeller/player.py` — **new module**; contains the `play(project)` function implementing
  the full command sequence, blocking loop, and shutdown handler. Imports `serialize` from
  `propeller.serializer` and `PropellerClient` from `propeller.transport`.
- `propeller/composition.py` — **updated**: `Project` gains a `play()` method that lazily
  imports and delegates to `propeller.player.play(self)`.
- `propeller/__init__.py` — **no change required**; `play` is accessed via `project_obj.play()`.

**Command sequence inside `play(project)`:**

```
serialize(project) → payload_dict
┌─ create-project ─────────────────────────────────────────────────────────┐
│  cmd = {"command": "create-project", **payload_dict}                     │
│  PropellerClient().send(json.dumps(cmd))                                 │
│    → success: continue                                                   │
│    → PropellerResponseError: raise immediately (loop-start NOT sent)     │
│    → PropellerConnectionError: raise immediately (loop-start NOT sent)   │
└──────────────────────────────────────────────────────────────────────────┘
┌─ loop-start ─────────────────────────────────────────────────────────────┐
│  PropellerClient().send(json.dumps({"command": "loop-start"}))           │
└──────────────────────────────────────────────────────────────────────────┘
┌─ blocking loop ──────────────────────────────────────────────────────────┐
│  try:                                                                    │
│      while True: time.sleep(1)                                           │
│  except KeyboardInterrupt:                                               │
│      ...shutdown handler...                                              │
└──────────────────────────────────────────────────────────────────────────┘
┌─ KeyboardInterrupt handler ──────────────────────────────────────────────┐
│  try:                                                                    │
│      PropellerClient().send(json.dumps({"command": "loop-stop"}))       │
│  except Exception:                                                       │
│      pass  # engine may have crashed — suppress silently                 │
│  sys.exit(0)                                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

**Command JSON format:**

- `create-project`: `{"command": "create-project", "header": {...}, "tracks": [...]}` —
  `serialize(project)` returns a dict with `"header"` and `"tracks"`; `play()` merges
  `{"command": "create-project"}` at the top level before serialising to JSON.
- `loop-start`: `{"command": "loop-start"}` — no additional fields.
- `loop-stop`: `{"command": "loop-stop"}` — no additional fields; send errors are suppressed.

Per Epic 2, each `PropellerClient().send(payload)` call owns its full connection lifecycle
(open → send newline-terminated UTF-8 → recv response → close). `play()` creates a fresh
`PropellerClient()` instance per command and does not manage sockets directly.

**Exit behaviour:** `sys.exit(0)` in the `KeyboardInterrupt` handler raises `SystemExit(0)`.
Python exits cleanly without printing a traceback for `SystemExit`, satisfying NF-3 and NF-5.

**Socket path:** `PropellerClient` resolves the socket path from `PROPELLER_SOCK` (defaulting
to `/tmp/propeller.sock`) at import time in `propeller.transport`. `play()` is transparent to the
path; it just instantiates `PropellerClient()`. AC-4 and AC-5 are covered by Epic 2's transport
tests; Epic 5 unit tests mock `PropellerClient` entirely.

**Test isolation:** `mock.patch('propeller.player.PropellerClient')` replaces the class with a
mock callable. `mock_client.return_value.send.return_value = None` simulates success;
`mock_client.return_value.send.side_effect = PropellerConnectionError(...)` simulates failure.
The blocking loop is controlled by patching `propeller.player.time.sleep` with a `side_effect`
that raises `KeyboardInterrupt` on the first call.

---

## Components

### `propeller/player.py`

**`play(project) -> None`** — public entry point.

1. Calls `serialize(project)` to get the payload dict.
2. Sends `create-project` via `PropellerClient().send()`. If the call raises, the exception
   propagates uncaught (no suppression for non-shutdown errors).
3. Sends `loop-start` via `PropellerClient().send()`.
4. Enters `while True: time.sleep(1)`.
5. On `KeyboardInterrupt`: sends `loop-stop` (all exceptions suppressed via `except Exception:
   pass`), then calls `sys.exit(0)`.

Module-level imports: `json`, `sys`, `time`, `from propeller.serializer import serialize`,
`from propeller.transport import PropellerClient`.

### `propeller/composition.py` (updated)

`Project.play()` — new method added to the frozen dataclass. Lazily imports and delegates:

```python
def play(self):
    from propeller.player import play as _play
    _play(self)
```

The lazy import avoids a circular dependency: `composition.py` is imported by `serializer.py`
indirectly (via duck typing), and `player.py` imports `serializer.py`. Deferring the import
to call time breaks the cycle.

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `create-project` command | `"command": "create-project"`, `"header": dict`, `"tracks": list` | Built in `play()` by merging `{"command": "create-project"}` with `serialize(project)` output. |
| `loop-start` command | `"command": "loop-start"` | Minimal; no additional fields. |
| `loop-stop` command | `"command": "loop-stop"` | Minimal; send errors silently suppressed during shutdown. |
| `PropellerResponseError` | `code: str` | Defined in `propeller/errors.py` (Epic 2); raised by `PropellerClient.send()` on engine error response; propagates uncaught from `play()` for `create-project`. |
| `PropellerConnectionError` | — | Defined in `propeller/errors.py` (Epic 2); raised by `PropellerClient.send()` on socket failure; propagates from `play()` for `create-project`; suppressed silently for `loop-stop`. |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID  | Task | Type | PRD ref | Depends on |
|-----|------|------|---------|------------|
| T-1 | Test: `from propeller.player import play` succeeds; `play` is callable | test | F-1 | — |
| I-1 | Create `propeller/player.py` with stub `play(project)` function; module-level imports: `json`, `sys`, `time`, `serialize`, `PropellerClient` | impl | F-1 | T-1 |
| T-2 | Test: `play(stub_project)` with mocked `PropellerClient` — first `send()` call receives a JSON string that deserialises to a dict with `"command": "create-project"`, `"header"`, and `"tracks"` keys | test | F-1, AC-1 | I-1 |
| I-2 | Implement `create-project` send in `play()`: call `serialize(project)`, merge `{"command": "create-project"}`, `json.dumps`, call `PropellerClient().send()` | impl | F-1, AC-1 | T-2 |
| T-3 | Test: when `create-project` send succeeds, a second `send()` call receives JSON `{"command": "loop-start"}` | test | F-2, AC-2 | I-2 |
| T-4 | Test: when `create-project` send raises `PropellerResponseError`, `send()` is called exactly once (no `loop-start`), and the error propagates to the caller | test | F-7, AC-7 | I-2 |
| I-3 | Append `loop-start` send in `play()` after successful `create-project`; natural sequential code satisfies F-7 (exception from step 1 aborts step 2) | impl | F-2, F-7 | T-3, T-4 |
| T-5 | Test: after `loop-start`, `time.sleep` is called; patch `time.sleep` with `side_effect=[None, KeyboardInterrupt]` and patch `PropellerClient` to succeed — verify `SystemExit` is eventually raised | test | F-3, NF-1, AC-3 | I-3 |
| I-4 | Add `while True: time.sleep(1)` blocking loop in `play()` after `loop-start` | impl | F-3, NF-1 | T-5 |
| T-6 | Test: patch `time.sleep` to raise `KeyboardInterrupt` on first call; verify `SystemExit(0)` is raised and the third `send()` call carries JSON `{"command": "loop-stop"}` | test | F-6, NF-3, AC-6 | I-4 |
| I-5 | Wrap `while True` loop in `try/except KeyboardInterrupt`; in handler: `PropellerClient().send(json.dumps({"command": "loop-stop"}))`, then `sys.exit(0)` | impl | F-6 | T-6 |
| T-7 | Test: same Ctrl+C setup, but `loop-stop` send raises `PropellerConnectionError`; verify `SystemExit(0)` is still raised, no exception propagates, and no output to stderr | test | F-9, NF-5, AC-8 | I-5 |
| I-6 | Wrap `loop-stop` send in `try/except Exception: pass` to silently suppress all errors | impl | F-9, NF-5 | T-7 |
| T-8 | Test: `PropellerConnectionError` raised by `create-project` send propagates uncaught from `play()` (not absorbed by the shutdown handler) | test | F-8 | I-6 |
| T-9 | Test: `Project.play()` method exists and is callable; calling it with a patched `propeller.player.play` verifies delegation (assert inner `play` was called with the project instance) | test | UJ-1 | I-6 |
| I-7 | Add `play()` method to `Project` in `composition.py`; lazily import and call `propeller.player.play(self)` | impl | UJ-1 | T-9 |

---

## Open Questions

None — all questions resolved.

---

## Open Decisions

None — all decisions resolved.

---

## Revision Log

### Cycle 1 — Confidence: 70%
- Reconciled: nothing (spec created fresh from PRD)
- Added: D-1 (player.py vs composition.py placement), D-2 (mock.patch vs dependency injection)

### Cycle 2 — Confidence: 92%
- Reconciled: D-1 → A (standalone `player.py`; architecture already reflected this — no changes needed); D-2 → A (`mock.patch` strategy; test isolation section already reflected this — no changes needed)
- Added: nothing — specification is complete
