# Roadmap: Sync Mode for py-propeller Engine

Add a `sync` option to the `-s` CLI parameter so that py-propeller operates without sending loop-start and loop-stop commands to the socket, enabling external clock sources to control the loop lifecycle independently.

---

## Dependency graph

| Epic | Depends on | Can start in parallel with |
| ---- | ---------- | -------------------------- |
| EP-1 | —          | —                          |

---

## EP-1 — Sync Mode

When the `-s sync` flag is passed, py-propeller runs without issuing loop lifecycle commands to the socket. A user invoking the engine in sync mode sees it accept and sequence events normally, but the socket never receives `{"command": "loop-start"}` or `{"command": "loop-stop"}` messages — those commands are suppressed entirely for the duration of the session.

**Acceptance criteria**

- The `-s` parameter accepts `sync` as a valid value alongside any existing values; passing any other value behaves exactly as before.
- When started with `-s sync`, py-propeller does not send `{"command": "loop-start"}` to the socket at any point during the session.
- When started with `-s sync`, py-propeller does not send `{"command": "loop-stop"}` to the socket at any point during the session.
- When started without `-s sync`, loop-start and loop-stop behaviour is unchanged.
- Passing `-s sync` does not cause an error or unexpected exit.
