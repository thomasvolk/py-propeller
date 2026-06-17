# py-propeller Roadmap

## Vision

py-propeller is a Python client library for the propeller-engine, presented as an internal DSL. It enables musicians and developers to describe musical projects in readable Python code and send them to the propeller-engine for immediate playback.

---

## Parallel Work Streams

The roadmap is organized into two independent streams that can progress in parallel and converge at the integration phase:

- **Stream 1 — DSL & Domain Model**: defines the Python DSL and the musical domain objects
- **Stream 2 — Engine Connectivity**: defines the communication layer with the propeller-engine, independent of DSL design choices

---

## Phase 1 — Foundation

*Stream 1 and Stream 2 run fully in parallel.*

### Epic 1 — Note Primitives DSL (Stream 1)

Define the building blocks of the DSL: note constants, duration, velocity, and rests.

**Acceptance criteria:**

- Note constants (C4, Cs4, Ef4, etc.) cover all MIDI pitches across all relevant octaves
- Duration modifier (`note * beats`) adjusts how long a note plays
- Velocity modifier (`note + amount`, `note - amount`) adjusts loudness
- Rest (`Z`) is a first-class value with duration support
- Modifiers compose correctly (e.g., `(C4 + 30) * 2`)
- All constants are importable via `from propeller.notes import *`

---

### Epic 2 — Socket Transport Layer (Stream 2)

Implement the low-level communication with the propeller-engine socket interface.

**Acceptance criteria:**

- A client can connect to the engine via socket with configurable host and port
- A raw JSON payload can be sent to the engine
- The client handles acknowledgement and error responses from the engine
- The connection lifecycle (open, send, close) has a well-defined contract
- The transport layer has no dependency on the DSL or domain model

---

## Phase 2 — Composition & Serialization

*Epic 3 and Epic 4 run in parallel. Epic 4 may start with a stub domain model while Epic 3 is in progress.*

**Depends on:** Epic 1 (for Epic 3), Epic 2 (for Epic 4 independently)

### Epic 3 — Composition Model (Stream 1)

Define the `track` and `project` domain objects that assemble notes into a full musical piece.

**Acceptance criteria:**

- `track()` accepts a name, MIDI channel, instrument, and a list of bars
- Each bar is an ordered list of notes produced by the note primitives from Epic 1
- `project()` accepts BPM, time signature, and a list of tracks
- All composed values are inspectable as plain Python objects

---

### Epic 4 — JSON Serialization (Stream 2)

Transform a composed project into the propeller JSON format required by the engine.

**Acceptance criteria:**

- A project object serializes to a valid propeller JSON payload
- Output conforms to the propeller-engine JSON socket interface specification
- Serialization is decoupled from transport: it returns data, it does not send
- All note attributes (pitch, duration, velocity, rest) map correctly to JSON fields

---

## Phase 3 — Integration & Playback

**Depends on:** Epic 3 and Epic 4

### Epic 5 — Play Loop & Script Lifecycle

Wire together the DSL, serialization, and transport into the `.play()` method.

**Acceptance criteria:**

- `project(...).play()` serializes the project and sends it to the engine
- The script blocks after sending and remains running until interrupted
- The socket path is configurable via `PROPELLER_SOCK` without code changes
- Clean shutdown on interrupt (e.g., Ctrl+C) is handled gracefully
- Running with `-n` prints JSON payloads to stdout and exits immediately without connecting to the engine

---

## Phase 4 — Quality & Developer Experience

*Epic 6 and Epic 7 are independent and can run in parallel with each other, and partly in parallel with Phase 3.*

### Epic 6 — Validation & Error Feedback

Add meaningful validation so DSL users receive helpful errors early.

**Acceptance criteria:**

- Invalid note values are caught with a descriptive, actionable message
- Invalid track or project structure raises a clear error before any network call
- Connection failures produce actionable messages rather than raw socket errors

---

### Epic 7 — Packaging & Public API

Ensure the library is installable and usable as a standalone Python package.

**Acceptance criteria:**

- The package is installable via pip
- `from propeller.notes import *` and `from propeller import project, track` work as shown in the briefing
- A minimal usage example ships with the package

---

## Dependency Map

```
Epic 1 (Note Primitives)          Epic 2 (Socket Transport)
        |                                  |
Epic 3 (Composition Model)    Epic 4 (JSON Serialization)
         \                                /
              Epic 5 (Play Loop)
                      |
     Epic 6 (Validation)    Epic 7 (Packaging)
```

---

## Summary Table

| Epic | Stream         | Phase | Depends on      | Can run in parallel with |
| ---- | -------------- | ----- | --------------- | ------------------------ |
| 1    | DSL            | 1     | —               | Epic 2                   |
| 2    | Connectivity   | 1     | —               | Epic 1                   |
| 3    | DSL            | 2     | Epic 1          | Epic 4                   |
| 4    | Connectivity   | 2     | Epic 2          | Epic 3                   |
| 5    | Integration    | 3     | Epic 3, Epic 4  | —                        |
| 6    | Quality        | 4     | Epic 5          | Epic 7                   |
| 7    | Quality        | 4     | Epic 5          | Epic 6                   |
