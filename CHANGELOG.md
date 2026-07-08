# Changelog

## [0.4.0] — 2026-07-08

### Added

- New `-s sync` mode: sends `create-project` to the engine and exits immediately, without ever sending `loop-start` or `loop-stop`, so an external clock source (a DAW or hardware sequencer) can own the transport lifecycle while py-propeller only delivers project data.

---

## [0.3.0] — 2026-07-07

### Added

- Serialization now raises `PropellerValidationError` when two lanes of the same track produce a pitch bend at the same tick offset, preventing ambiguous MIDI output.

### Fixed

- Pitch bends placed in lanes that contain only rests and pitch bend elements are now correctly included in the serialized output at their proper tick offsets; previously they were silently discarded.
- All pitch bends in a PB-only lane are emitted when multiple pitch bends are separated by rests; previously only the last pending pitch bend was kept and intermediate ones were silently overwritten.

### Internal

- Added technical specification and dedicated test suite for pitch bend lane combination behaviour.

---

## [0.2.0] — 2026-07-07

### Added

- Pitch bend support: the sequencer can now send MIDI pitch bend messages, enabling expressive pitch modulation in generated sequences.
- Pitch bend example demonstrating how to use the new pitch bend API.

---
