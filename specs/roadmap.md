# Roadmap: General MIDI Drum Note Constants

Provide a set of named constants for General MIDI drum sounds so that drum
parts can be written using descriptive names instead of raw MIDI note
numbers.

---

## Dependency graph

| Epic | Depends on | Can start in parallel with |
| ---- | ---------- | --------------------------- |
| EP-1 | —          | —                            |

---

## EP-1 — General MIDI Drum Note Constants

Delivered as the `propeller.notes.drums` module. A user composing a drum
part can reference each General MIDI Level 1 drum sound by a descriptive,
readable name instead of memorizing its numeric MIDI note value.
Every name is derived directly from the standard General MIDI
drum sound name by removing spaces. Drum sounds that were only added in
General MIDI Level 2 are left out where doing so does not create ambiguity
or gaps that would confuse a user reading the available names.

**Acceptance criteria**

- A distinct, importable, named constant exists for every General MIDI
  Level 1 drum sound in the range of note numbers 27 through 87.
- Each constant's name matches its standard General MIDI drum sound name
  with all spaces removed (for example, "Bass Drum 2" is available as
  `BassDrum2`).
- Each constant resolves to the correct MIDI note number for that drum
  sound.
- Drum sounds tagged as General MIDI Level 2 additions are omitted from the
  available constants wherever omitting them does not prevent a Level 1
  drum sound from being represented.
- A user can discover the complete set of available drum names without
  needing to consult external documentation.
