# EP-2 · Concurrent Slide Consolidation — Technical Specification

## Overview
This epic makes concurrent `Slide`s on the same track compose correctly: when two or more Slides
produce pitch-bend events at the same tick, matching values collapse into a single event, mismatched
values are rejected as invalid, and collisions involving a manually-placed `PitchBend` note keep
today's error behaviour. Note placement and cross-track isolation are unaffected.

**Confidence Level:** 90% — this epic is a comparatively narrow, well-constrained extension of EP-1's
already-settled architecture (D-1, atomic Slide expansion in `propeller/serializer.py`); every F-x/AC-x
maps to a concrete rule with no remaining architectural branch points. Confidence is capped just under
full certainty because the exact wording of the new validation error message is left to
implementation-time judgement rather than specified here (a cosmetic detail, not a behavioural one).

---

## Architecture Overview

This epic touches only `propeller/serializer.py`, building directly on EP-1's `_expand_slide` /
`_serialize_lane` design rather than introducing new public types.

**1. Origin tagging in `_serialize_lane`.** Every pitch-bend row `_serialize_lane` accumulates is
tagged with where it came from: `'manual'` for a row flushed from a literal `PitchBend` item already in
the lane (both the note-triggered flush and the `emit_trailing_pb` trailing flush — these code paths
are unchanged otherwise), and `'slide'` for rows returned by `_expand_slide` (EP-1, D-1 option A). This
changes `_serialize_lane`'s pitch-bend return elements from `[tick, value]` pairs to `(tick, value,
source)` triples. Note accumulation (`notes_out`) is untouched.

**2. Grouped consolidation in `_serialize_track`.** The multi-lane branch replaces its current blanket
`len(ticks) != len(set(ticks))` check with a per-tick consolidation pass over the combined
`(tick, value, source)` rows from all lanes:
- A tick with exactly one contributing row passes through unchanged (F-5/AC-5).
- A tick with more than one row keeps exactly one `[tick, value]` output row **only if** every row at
  that tick has `source == 'slide'` **and** all their values are equal (F-1/AC-1).
- Otherwise (any row is `'manual'`, or two or more `'slide'` rows disagree on value), the whole
  serialization raises `PropellerValidationError` — this single rule covers both F-4/AC-4 (mismatched
  Slide values) and F-6/AC-6 (any manual involvement) without needing to special-case them separately.

Before rows reach the final JSON `pitch-bends` array, the `source` tag is stripped in **both** branches
of `_serialize_track` (the single-lane branch also needs a trivial tag-strip, since `_serialize_lane`'s
return shape changes for all callers, even though a single lane can never collide with itself under the
existing "no consecutive PitchBend" rule, so it needs no consolidation logic of its own).

**3. Everything else is a no-op by construction.** F-2/AC-2 (notes unaffected) and F-3/AC-3
(per-track scoping) require no new logic: `notes_out` accumulation isn't touched by this epic, and
`_serialize_track` already processes one track at a time with no cross-track state. These are covered
below by regression tests rather than new implementation.

---

## Components

### `_serialize_lane` (propeller/serializer.py, modified)
Adds a `source: 'manual' | 'slide'` tag to each pitch-bend row it accumulates, at both existing manual
`PitchBend`-flush sites and the `_expand_slide` call site. No other behaviour changes.

### `_serialize_track` (propeller/serializer.py, modified)
- Single-lane branch: strips the `source` tag before assigning `pitch_bends_out` — no consolidation
  needed.
- Multi-lane branch: replaces the blanket tick-collision check with the grouped consolidation pass
  described above, producing a de-duplicated, tag-stripped, tick-sorted `pitch_bends_out` list.

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| internal pitch-bend row (not a public class) | `tick: int`, `value: int`, `source: 'manual' \| 'slide'` | Used only inside `propeller/serializer.py` between `_serialize_lane` and `_serialize_track`; the `source` tag is stripped before the row enters the final JSON `pitch-bends` output |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers. New tests live
in `tests/test_slide_consolidation.py` (the names `test_ep1_lane_combination.py` / `test_ep2_serializer.py`
are already used by unrelated, pre-existing work and must not be reused or modified).

| ID | Task | Type | PRD ref | Depends on |
|----|------|------|---------|------------|
| T-1 | Test `_serialize_lane` tags pitch-bend rows `source='manual'` for a literal `PitchBend` item (both note-triggered and trailing flush) and `source='slide'` for rows produced by a `Slide` item | test | F-1, F-4, F-6 (groundwork) | — |
| T-2 | Add `source` tagging to `_serialize_lane`'s pitch-bend accumulation | impl | F-1, F-4, F-6 (groundwork) | T-1 |
| T-3 | Test two Slides in different lanes producing identical values at the same tick serialize to a single consolidated pitch-bend row | test | F-1, AC-1 | T-2 |
| T-4 | Implement the "all-slide, equal-value" dedup branch of `_serialize_track`'s consolidation pass | impl | F-1, AC-1 | T-3 |
| T-5 | Test each Slide's own Note events are identical whether serialized alone or alongside a concurrent Slide | test | F-2, AC-2 | T-4 |
| T-6 | Confirm (regression only — no production change expected) that note accumulation is unaffected by the consolidation pass | impl | F-2, AC-2 | T-5 |
| T-7 | Test Slides on two different tracks with overlapping timing don't affect each other's pitch-bend output | test | F-3, AC-3 | T-6 |
| T-8 | Confirm (regression only — no production change expected) that per-track scoping in `_serialize_track` is unaffected | impl | F-3, AC-3 | T-7 |
| T-9 | Test two Slides in the same track producing different values at the same tick raise `PropellerValidationError` | test | F-4, AC-4 | T-8 |
| T-10 | Implement the "slide values differ" error branch of the consolidation pass | impl | F-4, AC-4 | T-9 |
| T-11 | Test two Slides whose pitch-bend events fall at non-matching ticks all appear in the output, sorted in time order, with none merged | test | F-5, AC-5 | T-10 |
| T-12 | Confirm single-contributor ticks pass through the consolidation pass unchanged | impl | F-5, AC-5 | T-11 |
| T-13 | Test a Slide's pitch-bend event colliding with a manually-placed `PitchBend` note at the same tick raises `PropellerValidationError`, even when their values happen to match | test | F-6, AC-6 | T-12 |
| T-14 | Implement the "any row not `source == 'slide'`" branch of the consolidation pass so it always raises, regardless of value equality | impl | F-6, AC-6 | T-13 |
| T-15 | Test repeated serialization of the same set of concurrent Slides always produces an identical consolidated pitch-bend sequence | test | NF-1 | T-14 |
| T-16 | Confirm the consolidation pass uses only order-preserving structures (no nondeterministic grouping) | impl | NF-1 | T-15 |

---

## Open Questions

None.

---

## Open Decisions

None — this epic's architecture is fully determined by EP-1's D-1 (already resolved) plus the PRD's
explicit consolidation rules; no further high-impact choices remain.

---

## Revision Log

### Cycle 1 — Confidence: 90%
- Created technical specification from specs/EP-2.md PRD, building directly on EP-1's finalized D-1
  architecture (atomic Slide expansion in `propeller/serializer.py`).
- Added: none — every F-x/AC-x/NF-1 resolves to a concrete rule with no remaining architectural branch
  points; specification is complete on the first pass.
