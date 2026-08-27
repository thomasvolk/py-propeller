# py-propeller

Python DSL client for [propeller-engine](https://github.com/thomasvolk/propeller-engine) — write musical compositions in Python and send them to the engine for immediate MIDI playback.

Describing a propeller-engine project as raw JSON is verbose and error-prone. py-propeller gives you a Pythonic notation for notes, durations, velocities, tracks, and timing, then handles serialization and socket transport to the engine automatically.

## Quick example

```python
from propeller.notes import *
from propeller import project, track

project(
    bpm=120,
    time_signature=(4, 4),
    bars=2,
    tracks=[
        track(
            name="Piano",
            channel=1,
            instrument=0,
            notes=[
                C4(120) * 2,    # middle C, velocity 120, held for 2 beats
                D4()    * 0.5,
                E4()    * 0.5,
                F4(),
                E4(120) * 2,
                Ds4()   * 0.5,
                Ef4()   * 0.5,
                Cs4()   * 1,
            ],
        )
    ],
).play()
```

Save the script and run it. It loops until you press Ctrl+C:

```
python my_project.py
```

## Installation

Requires Python 3.11 or later and a running propeller-engine instance (>=0.8.0 — earlier engine versions used a mixed `"command"`/`"type"` IPC tagging scheme that this client's wire format does not send; 0.8.0 is also the minimum version providing the `get-position` response format that `propeller.loop.get_position()` relies on).

1. Install the package:

   ```
   pip install py-propeller
   ```

2. Start the propeller-engine (see the [engine documentation](https://github.com/thomasvolk/propeller-engine) for setup steps).

3. Run your composition script.

## Usage

### Note constants

Every MIDI pitch is available as a pre-built constant in `propeller.notes`. The naming convention is `<Note><Octave>`, with sharps written as `s` and flats as `f`:

| Constant       | Meaning              | MIDI pitch |
| -------------- | -------------------- | ---------- |
| `C4`           | middle C, octave 4   | 60         |
| `Cs4` / `Df4` | C♯ / D♭, octave 4   | 61         |
| `Ef4` / `Ds4` | E♭ / D♯, octave 4   | 63         |

Constants cover octaves 0–8. Import them all at once:

```python
from propeller.notes import *
```

### Drum note constants

General MIDI percussion sounds (note numbers 35–81) are available as pre-built `Note` constants in `propeller.notes.drums`, named after their General MIDI Level 1 drum sound with spaces and hyphens removed:

| Constant       | Meaning        | MIDI pitch |
| -------------- | -------------- | ---------- |
| `BassDrum1`    | Bass Drum 1     | 36         |
| `SnareDrum1`   | Snare Drum 1    | 38         |
| `ClosedHihat`  | Closed Hi-hat   | 42         |
| `OpenHihat`    | Open Hi-hat     | 46         |
| `Cowbell`      | Cowbell         | 56         |

Import them all at once, alongside pitch constants:

```python
from propeller.notes import *
from propeller.notes.drums import *
```

Drum constants are ordinary `Note` values, so the same duration and velocity modifiers apply. General MIDI reserves channel 10 for percussion:

```python
from propeller.notes.drums import SnareDrum1, ClosedHihat

track(
    name="Drums",
    channel=10,
    instrument=0,
    notes=[
        ClosedHihat(90) * 0.5,
        ClosedHihat(90) * 0.5,
        SnareDrum1(110),
    ],
)
```

See `examples/drum_example.py` for a full example.

General MIDI Level 2 percussion additions (e.g. Shaker, Sticks) are not included.

### Duration and velocity

Multiply a note by a beat count to set its duration. Call a note with a velocity value (0–127) to override the default of 100:

```python
C4            # 1 beat, velocity 100 (defaults)
C4 * 2        # 2 beats
C4 * 0.5      # half a beat
C4(120)       # velocity 120
C4(120) * 2   # velocity 120, 2 beats
```

### Rests

`Z` (or lowercase `z`) is a rest. It supports the same duration modifier:

```python
Z       # 1-beat rest
Z * 2   # 2-beat rest
```

### Tracks and projects

```python
from propeller import project, track

p = project(
    bpm=140,
    time_signature=(3, 4),
    bars=4,
    tracks=[
        track(name="Bass", channel=1, instrument=32, notes=[C2 * 2, Z, G2]),
    ],
)
p.play()
```

- `channel` — MIDI channel, 1–16
- `instrument` — General MIDI program number, 0–127
- `bpm` — beats per minute (positive float)
- `time_signature` — `(numerator, denominator)`, both positive integers. `numerator` is how many beats make up one bar. `denominator` sets the beat unit: `4` for a quarter-note beat, `8` for an eighth-note beat, `16` for a sixteenth-note beat, and so on — a unit-duration note (e.g. `C4`) always lasts exactly one beat, so changing the denominator changes how long that note plays in real time.
- `bars` — number of bars to loop (positive integer); purely informational and not cross-validated against note content

### Overlapping notes (chords and polyphony)

Pass `notes` as a list of lists to define multiple independent lanes within a single track. Each lane accumulates its own tick cursor from zero, so notes in different lanes can start at the same tick:

```python
track(
    name="Piano",
    channel=1,
    instrument=0,
    notes=[
        [C4() * 2],   # lane 1 — starts at tick 0
        [E4() * 2],   # lane 2 — starts at tick 0
        [G4() * 2],   # lane 3 — starts at tick 0
    ],
)
```

A more complex example — melody in one lane, sustained bass note in another:

```python
track(
    name="Piano",
    channel=1,
    instrument=0,
    notes=[
        [C4(), D4(), E4(), F4()],   # melody lane
        [C3() * 4],                  # bass lane, held for 4 beats
    ],
)
```

A flat `notes=[...]` list continues to work as a single lane. The two forms cannot be mixed within the same track.

### Pitch bend

`PB(value)` inserts a pitch bend event into a note sequence. `value` ranges from `-1.0` (full bend down) through `0.0` (centered) to `1.0` (full bend up):

```python
from propeller.notes import *

track(
    name="Lead",
    channel=1,
    instrument=0,
    notes=[
        PB(0.0),  C4(100),
        PB(0.5),  C4(100),
        PB(-0.5), C4(100),
    ],
)
```

A pitch bend fires at its own position in the sequence and does not itself consume any duration — placing a rest between a `PB(...)` and the next note delays the note, not the bend. Consecutive `PB(...)` calls with no note or rest between them are not permitted. See `examples/pitch_bend_example.py` for a full example.

### Pitch slide

`Slide(note, target)` plays `note` once and glides its pitch bend continuously across the slide's
duration, following the shape given by `target`:

```python
from propeller.notes import C4, D4, E4, Slide
from propeller.notes.Slide import to, sin, cos, gauss  # slide curve factories

track(
    name="Lead",
    channel=1,
    instrument=0,
    notes=[
        Slide(C4, to(1.0, steps=0.01)) * 4,      # play C4 and bend up to the max over 4 beats
        Slide(C4, to(-0.5)) * 4,                  # play C4 and bend down to half, default steps
        Slide(D4, sin(amp=1, period=2)) * 4,      # a sine wave slide, one full cycle
        Slide(D4, cos(amp=1, period=2)) * 4,      # same, but starting from the peak
        Slide(E4, gauss(u=0, o=1)) * 4,           # a smooth 0 -> ~1 -> 0 bump
    ],
)
```

- `note` — the `Note` to play once for the slide's full duration.
- `target` — the slide's pitch-bend curve, one of:
  - `to(value, steps=0.01)` — glides linearly from `0.0` to `value`, where `value` is in
    `[-1.0, 1.0]` and not `0.0` (a slide has to actually move the pitch).
  - `sin(amp=2, period=1, y_offset=0, steps=0.01)` / `cos(amp=2, period=1, y_offset=0, steps=0.01)`
    — a sine/cosine wave: `amp * sin(p * period * pi) + y_offset` (respectively `cos`) as a function
    of the slide's progress `p` from `0.0` to `1.0`; `period` is in units of pi (`period=2` is one
    full cycle across the slide's duration).
  - `gauss(u=0, o=1, steps=0.01)` — a normalized standard-normal bump (peak scaled to `1.0`),
    sampled across a fixed `[u - 3*o, u + 3*o]` window as progress runs `0.0` to `1.0`, so it always
    starts near `0`, peaks near `1`, and returns near `0` within the slide.
  - a plain function `progress -> value` (e.g. `def my_curve(ctx): ...`, or a lambda), passed
    directly as `target` for a fully custom shape — sampled at the default `steps` interval (`0.01`).
  - In every case, `steps` is the time-domain sampling interval: the fraction of the slide's progress
    between consecutive pitch-bend events, in `(0.0, 1.0]`, defaulting to `0.01` (~100 events across
    the slide). Larger `steps` values produce fewer, more audible steps. Any curve value outside
    `[-1.0, 1.0]` is clipped to the nearest boundary rather than raising an error.
- Multiply by a beat count, like any other note, to set the slide's total duration: `Slide(C4, to(1.0)) * 4`.

The pitch bend is reset to zero at the start of the slide and again at its end, so a glide never leaves
the channel's pitch wheel offset for whatever note plays next. If a `Slide` or `PB` produces a
pitch-bend event at the same tick offset as another one earlier in the same lane, only the earlier one
takes effect — the later one is dropped.

Two concurrent slides in different lanes of the same track (a multi-lane `notes=[[...], [...]]` track) have their pitch-bend events consolidated automatically instead of conflicting, as long as they agree at every shared tick. See `examples/slide_example.py` for a full example.

### Conditional notes

`probability(p, note, replacement=Z)` resolves to `note` with probability `p` (`0.0`–`1.0`) and to `replacement` otherwise (a rest, `Z`, by default):

```python
from propeller.notes.drums import SnareDrum1, HandClap
from propeller.func import probability

probability(0.5, SnareDrum1, replacement=HandClap)   # 50/50 snare or hand clap
probability(0.5, SnareDrum1)                          # 50/50 snare or rest
```

The outcome is rolled once, when the script is evaluated — running it once via plain `python` freezes the choice for the whole playback. Run it with `py-propeller` (see Live setup below) to re-roll on every reload. See `examples/probability_example.py` for a full example.

### Value-based selection

`selection(value)` picks a value based on where `value` falls relative to a set of thresholds — useful for varying a part by loop count, tick, or any other comparable value:

```python
from propeller.func import selection
from propeller.notes import C4, D4, E4, F4

piano_line = (
    selection(loop_count)
    .before(5,  [C4, D4, E4, F4])
    .after(5,   [C4, D4, E4, F4])
    .after(6,   [C4, D4, D4, C4])
    .after(20,  [C4, D4, E4, C4])
    .default(   [C4, D4, E4, C4])
    .select()
)
```

- `.before(threshold, value)` matches when `value < threshold`
- `.after(threshold, value)` matches when `value >= threshold`
- Conditions are tested in the order they're declared and the *first* match wins — so a later, narrower condition (e.g. `.after(20, ...)` following `.after(5, ...)`) is only reachable if nothing earlier already matched
- `.default(value)` is returned if nothing matches; if no default is set, `.select()` returns `None`
- The threshold passed to `.before()`/`.after()` must be comparable to `value` (e.g. both numbers, or both dates) — an incomparable threshold raises `PropellerValidationError`

`value` is a plain, already-resolved value (e.g. `loop.get_position().loop_count`), not a callable — for a value that changes over time, build a new `selection(...)` on each evaluation. See `examples/selection_example.py` for a full example.

### Transport configuration

py-propeller connects to the engine via Unix domain socket at `/tmp/propeller.sock` by default. Override with an environment variable:

```
PROPELLER_SOCK=/var/run/propeller.sock python my_project.py
```

### Reading the loop position

`propeller.loop.get_position()` queries the engine for the current playback position:

```python
from propeller import loop

p = loop.get_position()
print(f"tick: {p.tick}")
print(f"loop_duration: {p.loop_duration}")
print(f"loop_count: {p.loop_count}")
```

- `tick` — current position within the loop, in ticks
- `loop_duration` — total loop length in ticks, or `None` if no project is loaded
- `loop_count` — number of loops completed since playback started

See `examples/position_example.py` for a full example.

### Reading engine status

`propeller.status.get_status()` queries the engine for its current status:

```python
from propeller import status

s = status.get_status()
print(f"status: {s.status}")
print(f"mode: {s.mode}")
print(f"midi_port_name: {s.midi_port_name}")
```

- `status` — `"ok"` (a non-`"ok"` response raises `PropellerResponseError` before `get_status()` returns)
- `mode` — `"standalone"`, `"clock"`, or `"sync"`
- `bpm` — current tempo
- `loop_duration` — total loop length in ticks, or `None` if no project is loaded
- `clock_state` — `"started"` or `"stopped"`
- `project_present` — whether a project is currently loaded
- `midi_port_name` — connected MIDI output port name, or `None` if not connected
- `sync_port_name` — connected sync port name, or `None` if not connected
- `sync_clock_state` — `"waiting"`, `"tracking"`, or `"lost"`, or `None` if not applicable

See `examples/status_example.py` for a full example.

### Playback lifecycle

`project(...).play()` sends a `create-project` command followed by `loop-start` and then blocks. Pressing Ctrl+C sends `loop-stop` and exits cleanly.

### Dry-run mode

Add `-n` to inspect the JSON payloads that would be sent to the engine without actually connecting:

```
python my_project.py -n
```

Each command is printed to stdout as a JSON line and the script exits immediately. Useful for debugging serialization before a live engine is available.

### Non-blocking mode

Pass `-s` with a state value to start or stop playback without keeping the script running:

```
python my_project.py -s active     # start or update the project
python my_project.py -s inactive   # stop the loop
python my_project.py -s sync       # push project data only; let an external clock own transport
```

`-s active` first queries the engine to check whether a project is already loaded. If none is present it sends `create-project`; if one exists it sends `modify-project`. Either way it follows up with `loop-start` and then exits immediately (exit code 0).

`-s inactive` sends `loop-stop` and exits immediately.

`-s sync` sends `create-project` and exits immediately. It never sends `loop-start` or `loop-stop`, so an external clock source — a DAW or hardware sequencer — retains full control of transport start and stop while py-propeller only delivers project data.

The `-s` flag has no effect when `-n` is also present — dry-run mode takes precedence.

### Live setup

Use the `py-propeller` command to get an instant feedback loop while composing. It re-reads and re-evaluates your script on a fixed interval — equivalent to running it with `-s active` on every tick — so every save is picked up automatically:

```
py-propeller examples/beat_example.py
```

While it's running, open `beat_example.py` in your editor and save changes — the engine will load the updated project within 100 ms, the default interval. Override it in milliseconds with `-n`:

```
py-propeller examples/beat_example.py -n 250
```

`py-propeller` blocks until interrupted. A mid-save syntax or runtime error is printed to stderr without stopping the watcher — fix the file and the next tick picks it up. Press Ctrl+C to send `loop-stop` and exit.

## Features

- Expressive note DSL: `C4(120) * 2`, `Ef4 * 0.5`, `Z * 4`
- All MIDI pitches across octaves 0–8 with sharp and flat aliases
- General MIDI drum/percussion note constants in `propeller.notes.drums` (e.g. `SnareDrum1`, `ClosedHihat`)
- Multi-lane tracks for chords and polyphony: `notes=[[C4()], [E4()], [G4()]]`
- Pitch bend support via `PB(value)` for expressive pitch modulation
- Pitch-bend glide via `Slide(note, target)`, with linear (`to`), sine/cosine (`sin`/`cos`), gaussian (`gauss`), and custom curve shapes, and automatic consolidation of concurrent slides across lanes
- Conditional/probabilistic notes via `probability(p, note, replacement=...)`
- Threshold-based value selection via `selection(value).before(...).after(...).default(...).select()`
- Validation at construction time with descriptive error messages
- JSON serialization to the propeller-engine wire format (PPQN 480)
- Unix socket transport with configurable path via `PROPELLER_SOCK`
- `propeller.loop.get_position()` to read the engine's current tick, loop duration, and loop count
- `propeller.status.get_status()` to read the engine's mode, tempo, clock state, and connected port names
- Graceful Ctrl+C shutdown
- Dry-run mode (`-n`) to print JSON payloads without connecting
- Non-blocking mode (`-s active` / `-s inactive`) for scripted start/stop
- `py-propeller` command for a live-reload feedback loop while composing
- Sync mode (`-s sync`) to hand transport control to an external clock source

## Contributing

Contributions are welcome. To report a bug or request a feature, open an issue at <https://github.com/thomasvolk/py-propeller/issues>. To contribute code, fork <https://github.com/thomasvolk/py-propeller>, make your changes on a branch, and open a pull request. Include tests for any new behaviour and follow the existing code style.

## Support

Open an issue in the project repository for questions or bug reports.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
