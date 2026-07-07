# Roadmap: Pitch Bend Support in py-propeller

Extend the py-propeller DSL with a `PB` element that lets composers place pitch-bend events within a note sequence, and have those events serialized into the propeller-engine JSON format and transmitted via socket.

---

## Dependency graph

| Epic | Depends on | Can start in parallel with |
| ---- | ---------- | -------------------------- |
| EP-1 | —          | —                          |
| EP-2 | EP-1       | —                          |

---

## EP-1 — Pitch Bend DSL Element

A composer can write `PB(value)` anywhere within a track's note list to declare a pitch-bend event. The argument is a float in the range -1.0 to 1.0, where -1.0 is maximum downward bend, 0.0 is no bend, and 1.0 is maximum upward bend. Using `PB` as a bare name (without calling it) is equivalent to `PB(0.0)`. A pitch-bend element carries no duration of its own; it is positionally associated with the note that immediately follows it in the sequence.

**Acceptance criteria**

- `PB(0.5)` placed before a note is accepted by the DSL without error.
- `PB` used as a bare constant is accepted and behaves identically to `PB(0.0)`.
- Values outside -1.0 to 1.0 are rejected with a descriptive error at parse or construction time.
- A `PB` element at the end of a note list (with no following note) is accepted without error.
- Multiple consecutive `PB` elements before a single note are accepted without error.
- A track with no `PB` elements behaves identically to current behaviour.

---

## EP-2 — Pitch Bend Serialization and Transmission

When a project is played, any pitch-bend elements in a track are included in the JSON payload sent to propeller-engine. Each bend is emitted as a two-element integer array `[tick, value]` inside the track's `pitch-bends` field. The tick is the offset from the start of the loop at which the bend occurs; the 14-bit integer value (0–16383) is derived from the DSL float, with 8192 representing no bend. Tracks without pitch-bend elements either omit the `pitch-bends` field or emit it as an empty list. The resulting payload is transmitted via socket in the same way as all other track data.

**Acceptance criteria**

- A track containing `PB(0.5)` before a note produces a `pitch-bends` entry whose tick equals the tick at which that bend was placed and whose value encodes 0.5 correctly as a 14-bit integer (value > 8192).
- `PB(0.0)` (and the bare `PB` constant) serializes to value 8192.
- `PB(-1.0)` serializes to value 0; `PB(1.0)` serializes to value 16383.
- The tick of each pitch-bend event is strictly less than the loop duration.
- A track with no `PB` elements produces no `pitch-bends` field, or an empty list.
- The full project JSON containing `pitch-bends` is transmitted to propeller-engine via socket and accepted without error.
- Existing projects without pitch bends continue to play correctly and produce no `pitch-bends` field in their output.
