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
            channel=0,
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

Requires Python 3.11 or later and a running propeller-engine instance.

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

- `channel` — MIDI channel, 0–15
- `instrument` — General MIDI program number, 0–127
- `bpm` — beats per minute (positive float)
- `bars` — number of bars to loop (positive integer)

### Transport configuration

py-propeller connects to the engine via Unix domain socket at `/tmp/propeller.sock` by default. Override with an environment variable:

```
PROPELLER_SOCK=/var/run/propeller.sock python my_project.py
```

### Playback lifecycle

`project(...).play()` sends a `create-project` command followed by `loop-start` and then blocks. Pressing Ctrl+C sends `loop-stop` and exits cleanly.

## Features

- Expressive note DSL: `C4(120) * 2`, `Ef4 * 0.5`, `Z * 4`
- All MIDI pitches across octaves 0–8 with sharp and flat aliases
- Validation at construction time with descriptive error messages
- JSON serialization to the propeller-engine wire format (PPQN 480)
- Unix socket transport with configurable path via `PROPELLER_SOCK`
- Graceful Ctrl+C shutdown

## Contributing

To report a bug or request a feature, open an issue in the project repository. To contribute code, fork the repository and open a merge request. Include tests for any new behaviour and follow the existing code style.

## Support

Open an issue in the project repository for questions or bug reports.

## License

No license has been specified. Contact the author at info@thomasvolk.de for terms of use.
