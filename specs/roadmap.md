# Roadmap: Time Signature Support

Changing the time signature currently has no observable effect on composition. This roadmap
covers making the time signature a real, respected setting that determines how many beats
make up a bar and what note value counts as one beat.

---

## Dependency graph

| Epic  | Depends on | Can start in parallel with |
| ----- | ---------- | --------------------------- |
| EP-1  | —          | —                            |

---

## EP-1 — Time Signature Governs Bar Length

A composer sets a time signature as a pair of numbers, and the system uses both numbers
to determine how a bar is measured: the first number is how many beats make up one bar,
and the second number is which note value counts as one beat. Once set, the time signature
changes how many notes of a given duration are needed to fill a bar, and this is observable
in the resulting composition — it is no longer ignored.

**Acceptance criteria**

- Given `time_signature=(4, 4)`, a bar contains 4 beats, each beat is a quarter note, and
  four consecutive quarter notes (`C4 * 4`) exactly fill one bar.
- Given `time_signature=(8, 8)`, a bar contains 8 beats, each beat is an eighth note, and
  eight consecutive eighth notes (`C4 * 8`) exactly fill one bar.
- Given `time_signature=(4, 8)`, a bar contains 4 beats, each beat is an eighth note, and
  four consecutive eighth notes (`C4 * 4`) exactly fill one bar.
- Given `time_signature=(8, 4)`, a bar contains 8 beats, each beat is a quarter note, and
  eight consecutive quarter notes (`C4 * 8`) exactly fill one bar.
- Changing the time signature changes where bar boundaries fall for a composition of a
  given set of notes, compared to leaving it at its previous value.
