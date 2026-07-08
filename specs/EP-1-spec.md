# EP-1 · Sync Mode — Technical Specification

## Overview

This epic adds a `sync` value to the `-s` CLI parameter. When `-s sync` is set, `play()` sends the `create-project` command (with the serialized project payload) to the propeller-engine socket and exits immediately, without ever sending `loop-start` or `loop-stop`. This lets an external clock source own the transport lifecycle while py-propeller only handles project delivery.

**Confidence Level:** 97% — every F-x/AC-x in the PRD maps to a TDD-ordered task, architecture and data model are unambiguous, and the one open decision (state representation) has been resolved; no blocking ambiguities remain.

---

## Architecture Overview

No new components, modules, or transport behaviour are introduced. `sync` is a third dispatch branch inside the existing `play()` function in `propeller/player.py`, following the same shape as the existing `-s inactive` and `-s active` branches:

1. `_parse_state()` (already present) extracts the raw string following `-s` from `sys.argv`. It performs no validation today — any string, including `"sync"`, passes through unchanged. No change to this function is required for F-1; recognising `"sync"` is achieved purely by adding a new `if state == 'sync':` branch in `play()`.
2. The `-n` dry-run check in `play()` runs *before* `_parse_state()` is consulted, so `-n` continues to take precedence over `-s sync` automatically — no code change needed for that interaction (mirrors existing precedence over `-s inactive`/`-s active`, see `TestDryRunPrecedenceOverStateInactive`/`Active`).
3. The new `sync` branch: serialize the project via the existing `serialize()` function, send a single `{"command": "create-project", **payload}` message via `PropellerClient().send(...)`, then `sys.exit(0)`. Unlike `-s active`, sync mode does **not** query `{"command": "status"}` or branch on `project_present` — F-5 requires `create-project` unconditionally, never `modify-project`.
4. No `loop-start`/`loop-stop` message is constructed or sent anywhere in the `sync` branch, satisfying F-2/F-3 by omission rather than by suppression logic.
5. Errors from `PropellerClient().send()` (e.g. `PropellerConnectionError`, `PropellerResponseError`) propagate uncaught, consistent with the existing `create-project` error-handling convention used by the default (no-flag) and `-s active` branches (see `TestCreateProjectError`, `TestConnectionErrorPropagates`). NF-1 only constrains behaviour for a *well-formed* project reaching a *reachable* engine — it does not require suppressing transport errors.

---

## Components

### Player Dispatcher (`propeller/player.py::play`)

Responsibility: given a `project` and `sys.argv`, decide which command sequence to send to the propeller-engine socket and whether to block. Adds one new branch:

```python
if state == 'sync':
    payload = serialize(project)
    PropellerClient().send(json.dumps({'command': 'create-project', **payload}))
    sys.exit(0)
```

Placed alongside the existing `inactive`/`active` checks, before the default (unconditional) blocking-loop branch. Reuses `serialize()` from `propeller/serializer.py` and `PropellerClient` from `propeller/transport.py` — no changes to either module.

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| `create-project` command (dict, JSON-serialized) | `command: "create-project"`, `header: {bpm, loop_duration}`, `tracks: [...]` | Unchanged shape produced by `serializer.serialize()`; reused as-is for sync mode (F-5) — no new fields |
| `state` (str) | one of `"inactive"`, `"active"`, `"sync"`, or `None` (unset/other) | Returned by `_parse_state()`; still a plain string, no enum introduced (see D-1) |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID | Task | Type | PRD ref | Depends on |
|----|------|------|---------|------------|
| T-1 | Add `TestStateSync` test class to `tests/test_player.py`: asserts exactly one `send()` call whose payload has `command == "create-project"` with `header`/`tracks` present (mirrors `TestStateActiveNoProject`), and that no call payload anywhere has `command in ("loop-start", "loop-stop")` | test | F-1, F-2, F-3, F-5, AC-1, AC-2, AC-5 | — |
| T-2 | Add test to `TestStateSync`: `play()` raises `SystemExit` with code `0` and `time.sleep` is never called (dependency mocked, matching `test_exits_immediately_with_code_zero` pattern from `TestStateActiveNoProject`) | test | F-6, AC-4, AC-6 | — |
| T-3 | Implement `sync` branch in `play()` (`propeller/player.py`): serialize project, send `create-project`, `sys.exit(0)` | impl | F-1, F-2, F-3, F-5, F-6 | T-1, T-2 |
| T-4 | Add `TestDryRunPrecedenceOverStateSync` to `tests/test_player.py` (mirrors `TestDryRunPrecedenceOverStateInactive`/`Active`): `-n` together with `-s sync` still emits the two dry-run JSON lines to stdout and opens no socket | test | F-4, AC-3 | T-3 |
| T-5 | Run full existing `tests/test_player.py` suite (`TestStateInactive`, `TestStateActiveNoProject`, `TestStateActiveWithProject`, default blocking-loop tests) to confirm no regression after the `sync` branch is added | test | F-4, AC-3 | T-3 |

---

## Open Questions

_None._

---

## Open Decisions

_None — D-1 resolved (option A: raw string comparison, already reflected in Architecture Overview and Data Model)._

---

## Revision Log

### Cycle 1 — Confidence: 88%
- Reconciled: nothing (first cycle, spec created from PRD)
- Added: D-1 (state value representation: raw string vs. typed enum)

### Cycle 2 — Confidence: 97%
- Reconciled: D-1 → confirmed option A (raw string comparison); no spec changes needed, architecture/data model already reflected this approach
- Added: nothing — specification is complete
