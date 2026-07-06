# Roadmap: Pitch Bend DSL Support

Extend the py-propeller DSL so composers can express pitch bends inline with note sequences, and have those bends delivered to propeller-engine in its native format. The end-state is a `PB` element that users place before a note in any track, with the project serialiser handling the float-to-MIDI conversion automatically.

---

## Dependency graph

| Epic | Depends on | Can start in parallel with |
| ---- | ---------- | -------------------------- |
| EP-1 | —          | —                          |
| EP-2 | EP-1       | —                          |

---

## EP-1 — Pitch Bend DSL Element

A `PB` element exists in the py-propeller DSL that composers place inside a track's note sequence to signal a pitch bend. Used as a bare name (`PB`) it means no bend (centre position); called with a float argument (`PB(0.5)`) it sets the bend amount in the range -1.0 (full downward) to 1.0 (full upward). Unlike notes, `PB` carries no duration and does not advance the playhead — it is a marker that attaches to whatever note follows it.

**Acceptance criteria**

- `PB(0.5)` produces a pitch bend element with value 0.5.
- `PB(-1.0)` and `PB(1.0)` are accepted as the extreme values.
- The bare name `PB` (no call) behaves identically to `PB(0.0)`.
- A `PB` element placed in a note list does not consume any time; the tick position of the following note is unchanged.
- Multiple `PB` elements may appear in a single note list, each before the note it is intended to affect.

---

## EP-2 — Pitch Bend Engine Serialisation

When a project containing `PB` elements is rendered to the engine format, each pitch bend appears in the correct track's `pitch-bends` array at the tick offset of the note that immediately follows it, with the float value converted to the engine's 14-bit integer representation. Tracks that contain no pitch bends include an empty `pitch-bends` list. The full round-trip — DSL source through `p.play()` — delivers pitch bend events to propeller-engine alongside the corresponding notes.

**Acceptance criteria**

- A `PB` placed immediately before a note is serialised with the same tick offset as that note.
- Float 0.0 serialises to integer 8192 (centre); -1.0 serialises to 0; 1.0 serialises to 16383; intermediate values are scaled proportionally.
- Every serialised tick value is less than the project's loop duration.
- A track with no `PB` elements includes `"pitch-bends": []` in its serialised form.
- Calling `p.play()` on a project with pitch bends sends those bends to propeller-engine without error.
