# Roadmap: Fix Pitch Bend Lane Combination

When a track has lanes that contain only pitch bends and rests, those pitch bends must
be merged into the final output at their correct time offsets alongside notes from other
lanes. The target end-state is that every `PB` value — regardless of which lane it
appears in or how many rests precede it — is present in the `pitch-bends` array with
the correct tick offset.

---

## Dependency graph

| Epic | Depends on | Can start in parallel with |
| ---- | ---------- | -------------------------- |
| EP-1 | —          | —                          |

---

## EP-1 — Pitch Bend Lane Combination

When a project is rendered, every pitch bend defined across all lanes of a track is
included in the output, not just those in the first lane. A pitch bend preceded by
rests appears at the tick offset those rests occupy, and pitch bends from different
lanes are merged and sorted by time. Notes and pitch bends from separate lanes are
combined without either being dropped or duplicated.

**Acceptance criteria**

- Given a track with a lane containing `[PB(0.0), D4 * 4]` and a lane containing `[Z, PB(0.5)]`, the rendered output contains both `[0, 8192]` and `[480, 12287]` in the `pitch-bends` array.
- Pitch bends from all lanes appear in the `pitch-bends` array sorted by ascending tick offset.
- Notes derived from note-bearing lanes are unaffected by the presence of pitch-bend-only lanes.
- A lane containing only `PB` and `Z` entries contributes no note events to the output.
- A project with no pitch bends renders an empty or absent `pitch-bends` array, unchanged from current behaviour.
