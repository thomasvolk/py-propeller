# Changelog

## [Unreleased]

## [0.8.0] — 2026-08-26

### Added

- `propeller.notes.Slide.sin()`, `.cos()`, and `.gauss()` — new pitch-bend curve generators for `Slide`, alongside the existing `to()`, plus support for passing a plain custom `progress -> value` function directly as a `Slide`'s target.

### Changed

- `Slide`'s `to(value, steps)`, `sin`/`cos`/`gauss`, and custom functions now share one curve-sampling mechanism in the serializer: `steps` is the time-domain sampling interval (fraction of the slide's progress between pitch-bend events) rather than a value-domain increment, so the number of pitch-bend events `to()` emits no longer scales with `value`'s magnitude. Curve values outside `[-1.0, 1.0]` are clipped instead of raising.

---

## [0.7.0] — 2026-08-21

### Added

- New `propeller.loop` module with a `get_position()` function that queries the engine for the current playback position, returning a `Position` with `tick`, `loop_duration` (`None` when no project is loaded), and `loop_count`.

### Fixed

- `PropellerClient.send()` and `.query()` no longer raise `KeyError` on engine responses that omit the `"status"` field entirely (as `get-position` responses do) — a missing `"status"` is now treated the same as `"status": "ok"`.

### Internal

- Requires propeller-engine >=0.8.0, the first version to support `get-position`.

---

## [0.6.0] — 2026-07-11

### Added

- New `propeller.notes.drums` module with named `Note` constants for every General MIDI Level 1 percussion sound (MIDI note numbers 35–81, e.g. `SnareDrum1`, `ClosedHihat`, `Cowbell`), usable directly in `Track` note lists alongside pitch constants. General MIDI Level 2 percussion additions are not included.

### Internal

- Added specification and dedicated test suite for the drum note constants module.
- `propeller/notes.py` restructured into a package (`propeller/notes/__init__.py`) to host the new `drums` submodule; the existing `propeller.notes` API is unchanged.

---

## [0.5.0] — 2026-07-08

### Changed

- The time signature's denominator now determines the beat unit (quarter, eighth, sixteenth, etc.) used when serializing note and rest durations and computing bar length; previously only the numerator had any effect and the denominator was silently ignored.

### Internal

- Added specification and dedicated test suite for time signature handling.

---

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
