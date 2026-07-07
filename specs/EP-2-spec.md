# EP-2 · Pitch Bend Serialization and Transmission — Technical Specification

## Overview

This epic implements the serializer side of pitch-bend support. When a project is serialized, any `PitchBend` elements in a track's note list are converted to `[tick, value]` integer pairs — where the value is a 14-bit integer derived from the DSL float via `int(round((dsl_float + 1.0) / 2.0 * 16383))` — and emitted as a `pitch-bends` array in the track's JSON dict. Tracks with no pitch-bend events omit the field entirely. No changes are required to the transport layer; the existing socket mechanism transmits the extended payload unchanged. EP-2 depends on EP-1 having established `PitchBend` in `notes.py` and `Track` validation in `composition.py`.

**Confidence Level:** 92% — all questions resolved; minor residual around the fact that EP-1's Track validation prevents consecutive PBs from reaching the serializer, so the serializer need not defend against that case, but this is an implicit dependency worth noting during implementation.

---

## Architecture Overview

A single module is modified: **`propeller/serializer.py`**. No changes are required to `player.py`, `transport.py`, or `composition.py`; the extended serialized dict is passed through the existing socket pipeline unchanged (F-6).

**`_serialize_lane`** is extended with a two-field pending-PB buffer — `pending_pb_value: float | None` and `pending_pb_tick: int` — initialized to `None` and `0` respectively:

1. When a `PitchBend` is encountered: record the current `tick_cursor` into `pending_pb_tick`, store the float value in `pending_pb_value`; do **not** advance `tick_cursor`.
2. When a `Note` is encountered with a pending PB: flush the PB as `[pending_pb_tick, _pb_to_int(pending_pb_value)]` — using the tick captured when the `PB` was first encountered, **not** the current `tick_cursor` — clear the buffer, then record the note entry normally.
3. When a `Rest` is encountered: advance `tick_cursor` as normal; the pending-PB buffer and its captured tick are unchanged. This means that for a `[PB, Rest, Note]` sequence the pitch-bend event fires at the position where the `PB` appeared, before the rest.
4. At end-of-lane with a pending PB still set: **silently discard** — no entry is emitted (F-8).

Because `PitchBend` carries no duration, in the common `[PB, Note]` case `pending_pb_tick` equals `tick_cursor` at the time the Note is processed; the captured-tick distinction only manifests when rests intervene between the PB and its following note.

`_serialize_lane` returns `(notes_out, pitch_bends_out)` — an internal breaking change from returning `list`. All callers are updated in the same commit.

**`_serialize_track`** is updated to unpack the two-tuple return. For single-lane tracks it uses the single `pitch_bends_out` directly. For multi-lane tracks it merges pitch-bend lists from all lanes and sorts the combined result by ascending tick (NF-2), consistent with how multi-lane note events are already merged. If the final list is non-empty, it adds a `pitch-bends` key (hyphen, matching the engine contract) to the track dict. If empty, the key is omitted (F-4, F-7).

A private helper **`_pb_to_int(value: float) -> int`** computes `int(round((value + 1.0) / 2.0 * 16383))`. Boundary contract: -1.0 → 0, 0.0 → 8192, 1.0 → 16383.

F-5 (each pitch-bend tick must be strictly less than loop duration) is a natural consequence of PBs firing at their own position in the sequence — a position that is necessarily before or at any following note's tick, which is itself bounded by `loop_duration` in a well-formed project. It is verified by tests rather than a runtime check.

---

## Components

### `_pb_to_int` helper (`propeller/serializer.py`)

Private function implementing `int(round((value + 1.0) / 2.0 * 16383))`. Boundaries: -1.0 → 0, 0.0 → 8192, 1.0 → 16383. Takes the DSL float directly; all range validation has already happened at construction time in `PitchBend.__post_init__`.

### Extended `_serialize_lane` (`propeller/serializer.py`)

Signature changes to return `tuple[list, list[list[int]]]`. Maintains a two-field pending-PB buffer (`pending_pb_value`, `pending_pb_tick`). When a `PitchBend` is encountered, the current cursor tick is captured and the value is stored; the cursor does not advance. When a `Note` is reached, the PB is flushed using the **captured** tick (not the note's tick), enabling PBs to fire at their declared position even when rests intervene. A trailing PB with no following `Note` is silently discarded (F-8).

### Extended `_serialize_track` (`propeller/serializer.py`)

Unpacks `(notes_out, pitch_bends_out)` from each `_serialize_lane` call. For multi-lane tracks, merges all per-lane `pitch_bends_out` lists and sorts the combined result by ascending tick. Adds `pitch-bends` (hyphen) to the track dict only when the merged list is non-empty.

### Transport layer (unchanged)

`player.py` and `transport.py` require no modifications. The serialized dict that `player.py` passes to `PropellerClient.send()` already contains the `pitch-bends` data after EP-2's serializer changes (F-6). AC-6 is tested by inspecting `serialize()` output directly, without a live socket connection (NF-3).

---

## Data Model

| Type | Fields | Notes |
|------|--------|-------|
| serialized pitch-bend entry | `[tick: int, value: int]` | `value = int(round((dsl_float + 1.0) / 2.0 * 16383))`; range 0–16383; 8192 = center/no-bend; tick = position where `PB` appears in sequence |
| track dict `pitch-bends` | `list[list[int]]` | JSON key uses hyphen; present only when non-empty; sorted by ascending tick |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID   | Task | Type | PRD ref | Depends on |
|------|------|------|---------|------------|
| T-1  | `serialize()` for `[PB(-1.0), note]` yields `pitch-bends` entry with value `0` | test | F-3, AC-3 | — |
| T-2  | `serialize()` for `[PB(0.0), note]` yields `pitch-bends` entry with value `8192` | test | F-3, AC-2 | — |
| T-3  | `serialize()` for bare `PB` before a note yields `pitch-bends` entry with value `8192` | test | F-3, AC-2 | — |
| T-4  | `serialize()` for `[PB(1.0), note]` yields `pitch-bends` entry with value `16383` | test | F-3, AC-3 | — |
| T-5  | `serialize()` for `[PB(0.5), note]` yields a `pitch-bends` value greater than `8192` | test | F-3, AC-1 | — |
| I-1  | Implement `_pb_to_int` and extend `_serialize_lane` / `_serialize_track` to emit 14-bit pitch-bend values | impl | F-1, F-2, F-3 | T-1–T-5 |
| T-6  | `serialize()` for `[PB(0.5), note]` at tick 0 yields `pitch-bends` entry with tick `0` | test | F-2, AC-1 | I-1 |
| T-7  | `serialize()` for `[note1(1 beat), PB(-0.5), note2]` yields pitch-bend at tick 480 (PB position = after note1, same as note2 start) | test | F-2 | I-1 |
| T-8  | `serialize()` for track with no `PB` elements has no `pitch-bends` key in the track dict | test | F-4, AC-5 | I-1 |
| T-9  | `serialize()` for track with trailing `PB` (no following note) has no `pitch-bends` key | test | F-8, AC-8 | I-1 |
| T-10 | `serialize()` with two `PB` events at different ticks yields `pitch-bends` sorted by ascending tick | test | NF-2 | I-1 |
| T-11 | Pitch-bend tick in `serialize()` output is strictly less than `loop_duration` for a PB before an in-range note | test | F-5, AC-4 | I-1 |
| T-12 | `serialize()` for a PB-free project produces output identical to the current serializer (no regressions) | test | F-7, AC-7 | I-1 |
| T-15 | `serialize()` for `[PB(0.5), rest(1 beat), note]` yields pitch-bend at tick `0` (PB position), not tick `480` (note position) | test | F-2 | I-1 |
| T-16 | Multi-lane track with `PB` in lane 1 and `PB` in lane 2 yields merged, tick-sorted `pitch-bends` list | test | F-1, NF-2 | I-1 |
| I-2  | Update `_serialize_track` to merge multi-lane pitch bends, sort by tick, and conditionally add `pitch-bends` | impl | F-1, F-4, F-7, F-8, NF-2 | T-6–T-16 |
| T-13 | `serialize()` result for a project with pitch bends has `pitch-bends` in the expected `[[tick, int], …]` format (AC-6 unit test) | test | F-6, AC-6, NF-3 | I-2 |
| T-14 | `serialize()` for a project with no `PB` elements is unchanged from the pre-EP-2 baseline (AC-7 regression) | test | F-7, AC-7 | I-2 |

---

## Open Questions

*(none)*

---

## Open Decisions

*(none)*

---

## Revision Log

### Cycle 1 — Confidence: 68%
- Reconciled: nothing (first cycle, spec created from PRD)
- Added: Q-1 (tick assignment for PB + Rest + Note), Q-2 (multi-lane pitch-bend merging)

### Cycle 2 — Confidence: 92%
- Reconciled: Q-1 → B: architecture updated (PB fires at its own tick, not the following note's tick; buffer captures `pending_pb_tick` at PB-encounter time; T-15 added to test `[PB, Rest, Note]` distinguishing case); Q-2 → A: multi-lane merge confirmed, T-16 added
- Added: nothing (confidence ≥ 90%)
