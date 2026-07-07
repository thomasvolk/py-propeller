# EP-1 · Pitch Bend Lane Combination — PRD

## Overview

When a project is rendered, every pitch bend defined across all lanes of a track must be
included in the output, not just those in lanes that happen to contain a note after the
pitch bend. A pitch bend preceded only by rests in its lane must appear in the
`pitch-bends` array at the tick offset accumulated by those rests. Pitch bends from all
lanes are merged and sorted by ascending tick offset; note events and pitch bend events
from separate lanes are combined without dropping or duplicating either.

**Confidence Level:** 90% — all roadmap requirements are covered, all acceptance criteria
are concrete and testable, and the two remaining edge cases (same-tick collision, multi-PB
PB-only lane) are now fully specified.

---

## User Journeys

### UJ-1 · Independent pitch bend lane

A composer writes a track with separate lanes: one or more note lanes carrying melody or
chords, and one or more PB-only lanes carrying pitch automation. Each PB-only lane uses
rests to place pitch bends at precise tick positions. When the project is serialized, the
pitch bends appear in the output at the correct times and affect all notes on the channel
exactly as the MIDI protocol specifies — the composer does not need to interleave pitch
bends inside the note lanes themselves.

---

## Functional Requirements

| ID  | Requirement |
| --- | ----------- |
| F-1 | A pitch bend that appears in a multi-lane track at a tick position not followed by any note in the same lane must still be included in the serialized `pitch-bends` array at that tick offset. |
| F-2 | All pitch bends collected from every lane of a track are merged into a single `pitch-bends` array and sorted by ascending tick offset. |
| F-3 | A lane that contains only `PB` and `Z` (rest) elements contributes no note events to the serialized output. |
| F-4 | Note events derived from note-bearing lanes are unaffected by the presence of PB-only lanes in the same track. |
| F-5 | A track with no pitch bends across any lane produces no `pitch-bends` key in the serialized output (existing behaviour preserved). |
| F-6 | If two or more lanes of a track produce a pitch bend at the same tick offset, the system raises `PropellerValidationError`. |
| F-7 | A PB-only lane containing multiple pitch bends separated by rests emits every pitch bend at its respective tick offset; none are silently dropped. |

---

## Non-Functional Requirements

| ID   | Requirement |
| ---- | ----------- |
| NF-1 | All existing passing tests must continue to pass; the fix must not regress any currently correct serializer or composition behaviour. |

---

## Acceptance Criteria

| ID   | Given | When | Then |
| ---- | ----- | ---- | ---- |
| AC-1 | A track with lane `[PB(0.0), D4 * 4]` and lane `[Z, PB(0.5)]` at 80 BPM, 4/4, 2 bars | the project is serialized | `pitch-bends` contains exactly two entries: `[0, 8192]` and `[480, 12287]`, sorted by ascending tick. |
| AC-2 | A track with pitch bends from two different lanes at different tick offsets | the project is serialized | the resulting `pitch-bends` array is sorted by ascending tick offset. |
| AC-3 | A lane containing only `[Z, PB(0.5)]` | that lane is serialized alongside note-bearing lanes | the lane contributes zero entries to the notes array. |
| AC-4 | A single-lane track ending with `[C4, PB(0.3)]` | the project is serialized | the trailing pitch bend is silently discarded and `pitch-bends` is absent (existing T-19 behaviour). |
| AC-5 | A track with no pitch bends in any lane | the project is serialized | the serialized track dict has no `pitch-bends` key. |
| AC-6 | A multi-lane track where two lanes each produce a pitch bend at tick 0 (e.g. `[PB(0.0), D4 * 4]` and `[PB(0.5), C4 * 4]`) | the project is serialized | `PropellerValidationError` is raised. |
| AC-7 | A PB-only lane `[PB(0.1), Z, PB(0.5), Z]` alongside a note-bearing lane | the project is serialized | `pitch-bends` contains entries `[0, 9011]` and `[480, 12287]`; neither is dropped. |

---

## Open Questions

*No open questions — PRD is complete.*

---

## Refinement Log

### Cycle 1 — Confidence: 65%
- Reconciled: nothing (EP-1.md did not previously exist)
- Added: Q1 (briefing PB value inconsistency), Q2 (same-tick collision), Q3 (multiple PBs in PB-only lane)

### Cycle 2 — Confidence: 75%
- Reconciled: Q1 → briefing fixed (`PB(0.2)` → `PB(0.5)`); integer `12287` was authoritative; AC-1 and AC-3 updated with concrete values; roadmap AC updated to match
- Remaining: Q2 (same-tick collision), Q3 (multiple PBs in PB-only lane)

### Cycle 3 — Confidence: 90%
- Reconciled: Q2 (D) → F-6 (same-tick collision raises PropellerValidationError) + AC-6; Q3 (A) → F-7 (all PBs in multi-PB PB-only lane emitted) + AC-7 (concrete values: `[0, 9011]`, `[480, 12287]`)
- Added: nothing — PRD is complete
