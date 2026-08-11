# Roadmap: Slide Note

Extend the composition language with a `Slide` note that glides audibly between a start pitch and an
end pitch. When complete, a composer can place a `Slide` among a track's notes and hear a smooth,
evenly-paced glide from one pitch to another, with correct behaviour even when several slides sound
on the same track at once.

---

## Dependency graph

| Epic | Depends on | Can start in parallel with |
| ---- | ---------- | --------------------------- |
| EP-1 | —          | —                            |
| EP-2 | EP-1       | —                            |

---

## EP-1 — Slide Note Playback

When a composer places a `Slide` between a start pitch and an end pitch among a track's notes, the
resulting output glides smoothly from the start pitch to the end pitch over the duration given to the
slide. The glide passes through every whole-tone note between the two pitches, spending an equal
share of the total duration on each one, and within each of those shares the pitch moves in small,
evenly-spaced steps rather than jumping. A `Slide` behaves like any other note: it can be given a
total duration and its output appears directly alongside other notes and pitch changes in the track.

**Acceptance criteria**

- Given a `Slide` from a start pitch to an end pitch, the output passes through every whole-tone note
  between the two pitches (inclusive of both endpoints), with each consecutive pair exactly one tone
  apart.
- The total duration given to the `Slide` is divided into equal-length shares, one per whole-tone
  interval identified above.
- Within each whole-tone interval's share of time, the pitch moves in a series of evenly-spaced
  increments no larger than the requested step size, so the glide from that interval's start note to
  its end note sounds continuous rather than stepped.
- The size of each pitch increment is computed on the assumption that the playback device's full
  pitch-bend range spans exactly one tone.
- A `Slide` can be given a total duration the same way a regular note can, and its resulting notes and
  pitch changes appear in the composition's output in the same place a regular note's would.

---

## EP-2 — Concurrent Slide Consolidation

Builds on [[EP-1]]. Because a pitch change affects an entire track rather than a single note, when two
or more slides on the same track sound at overlapping points in time, their pitch changes are merged
into one consistent sequence for the track instead of conflicting or duplicating. Each slide's own
notes still appear exactly as they would if it were the only slide sounding, so multiple simultaneous
slides can be composed without producing contradictory or redundant pitch movement.

**Acceptance criteria**

- Given two or more slides on the same track whose pitch changes fall at the same points in time, the
  output contains exactly one pitch change per point in time for that track, not one per slide.
- Each slide's own notes appear in the output exactly as they would if that slide were the only one
  present on the track.
- Slides on different tracks never affect each other's pitch changes, regardless of timing overlap.
