# EP-1 · Slide Note Playback — PRD

## Overview
When a composer places a `Slide` between a start pitch and an end pitch among a track's notes, the
resulting output glides smoothly from the start pitch to the end pitch over the duration given to the
slide. The glide passes through every whole-tone note between the two pitches, spending a time share
proportional to each interval's tonal width, and within each of those shares the pitch moves in small,
evenly-spaced steps rather than jumping. A `Slide` behaves like any other note: it can be given a
total duration and its output appears directly alongside other notes and pitch changes in the track.

**Confidence Level:** 93% — all four rounds of open questions are resolved (direction, partial-interval
handling, retriggered-note velocity, step-count rounding, and interval time-share). The only remaining
gaps are minor, unlisted edge cases (e.g. a zero-distance slide) that don't block implementation.

---

## User Journeys

### UJ-1 · Composing a single ascending slide
A composer writes `Slide(C4, C5, steps=0.1) * 4` inside a track's notes list, intending a smooth
quarter-note-by-quarter-note glide from C4 up to C5 across 4 beats. When the composition is rendered
and played, they hear one continuous upward glide rather than six separate re-picked notes.

### UJ-2 · Reusing a Slide like a regular note
A composer scales a `Slide`'s total duration with the same `* n` syntax used for `Note` and `Rest`,
and places it in a notes list next to ordinary notes, expecting it to occupy its slot in the track's
timeline exactly as a note would.

### UJ-3 · Sliding across a non-whole-tone distance
A composer writes `Slide(C4, Ds4, steps=0.1) * 2`, sliding a minor third rather than a whole number of
tones. They expect the glide to still move in even, continuous steps, ending precisely on Ds4 rather
than overshooting to the next whole-tone note, and to move at the same speed throughout rather than
slowing down on the final partial interval.

### UJ-4 · Sliding downward
A composer writes `Slide(C5, C4, steps=0.1) * 4`, expecting the pitch to glide smoothly downward from
C5 to C4, passing through the same whole-tone notes as the ascending case but in reverse order.

---

## Functional Requirements

| ID | Requirement |
|----|-------------|
| F-1 | A composer can construct a Slide by specifying a start note, an end note, and a step size, matching the shape `Slide(start, end, steps=value)`. |
| F-2 | The system identifies whole-tone steps from the start pitch to the end pitch, stepping in the direction of travel (ascending if the end pitch is higher, descending if lower); every step spans exactly one tone except possibly the final step, which spans only the remaining distance when the total distance between start and end isn't a whole number of tones. |
| F-3 | A Slide can be assigned a total duration the same way a Note can (e.g. via multiplication by a number of beats). |
| F-4 | The Slide's total duration is divided into shares proportional to each interval's tonal width (F-2), so that the glide's speed (tone per unit time) is constant throughout — a half-tone final interval receives half the time share of a full-tone interval. |
| F-5 | At the start of each interval (except the pitch reached by the final interval's bend), a Note event is triggered at that interval's starting pitch. |
| F-6 | Within each interval's share of time, a sequence of pitch-bend events is generated that moves the pitch, in equal increments no larger than the requested step size, from the interval's starting pitch to its ending pitch. |
| F-7 | Pitch-bend increments are computed on the assumption that the device's full pitch-bend range corresponds to exactly one tone. |
| F-8 | The notes and pitch-bend events produced by a Slide appear in the composition's output in the same position the Slide occupied among the track's notes. |
| F-9 | All Note events retriggered during a Slide (per F-5) use the start note's velocity; the end note's velocity has no effect on any generated note. |
| F-10 | When the pitch-bend step size does not evenly divide an interval's tonal distance, the number of pitch-bend events generated for that interval is rounded to the nearest whole number, absorbing the discrepancy rather than raising an error. |

---

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NF-1 | Given the same start pitch, end pitch, step size, and total duration, a Slide must always produce the same sequence of notes and pitch-bend events. |

---

## Acceptance Criteria

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | A Slide from C4 to C5 with steps=0.1 and a total duration of 4 beats | the composition is rendered | the output contains 6 Note events, one triggered at each of C4, D4, E4, Fs4, Gs4, and As4, each lasting one sixth of the total duration |
| AC-2 | The same Slide from AC-1 | the composition is rendered | each of the 6 Note events is followed by 10 evenly-spaced pitch-bend events that move the pitch from that interval's starting note to its ending note, so the last pitch-bend event of one interval coincides with the pitch of the next interval's starting note (or the Slide's end pitch, for the final interval) |
| AC-3 | A Slide assigned a total duration via multiplication (e.g. `* 4`) | the composition is rendered | the Slide's total time span equals that duration, the same way a Note's duration is set via multiplication |
| AC-4 | A Slide placed among a track's notes | the composition is serialized | the Slide's generated notes and pitch-bend events appear in the output at the position the Slide occupied, in the same structure as notes and pitch-bends written directly |
| AC-5 | A Slide from C4 to Ds4 (a minor third, 1.5 tones), steps=0.1 | the composition is rendered | the output contains one full whole-tone interval from C4 to D4, followed by one partial interval spanning only the remaining half-tone from D4 to Ds4, ending exactly on Ds4 |
| AC-6 | A Slide from C4 (velocity 80) to C5 (velocity 120), steps=0.1 | the composition is rendered | every retriggered Note event in the output has velocity 80, regardless of the end note's velocity |
| AC-7 | A Slide whose step size does not evenly divide an interval's tonal distance (e.g. steps=0.3) | the composition is rendered | the number of pitch-bend events generated for that interval is the nearest whole number to (interval distance / steps), with no validation error raised |
| AC-8 | A Slide from C5 to C4 (a descending slide), steps=0.1 | the composition is rendered | the whole-tone intervals step downward through C5, As4, Gs4, Fs4, E4, D4, ending at C4 |
| AC-9 | A Slide from C4 to Ds4 (1.5 tones total) with a total duration of 2 beats | the composition is rendered | the full-tone interval (C4 to D4) lasts two-thirds of the total duration and the half-tone interval (D4 to Ds4) lasts one-third of the total duration, so both intervals glide at the same tone-per-time rate |

---

## Open Questions

None — all open questions have been resolved as of Cycle 3.

---

## Refinement Log

### Cycle 1 — Confidence: 60%
- Created PRD from specs/roadmap.md EP-1 entry.
- Added: Q1 (non-whole-tone/descending slides), Q2 (retriggered note velocity), Q3 (rounding when
  values don't divide evenly).

### Cycle 2 — Confidence: 78%
- Reconciled: Q1 → F-2 (direction + partial final interval), AC-5, AC-8, UJ-3, UJ-4
- Reconciled: Q2 → F-9 (retriggered notes use start note's velocity), AC-6
- Reconciled: Q3 → F-10 (round pitch-bend step count to nearest whole number), AC-7
- Added: Q4 (time-share of a partial final interval), a gap surfaced by resolving Q1

### Cycle 3 — Confidence: 93%
- Reconciled: Q4 → F-4 (proportional time-share per interval, constant glide speed), AC-9, UJ-3 updated
- Added: none — PRD is complete; remaining gaps are minor unlisted edge cases (e.g. zero-distance
  slide) that don't warrant blocking questions.
