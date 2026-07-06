# Goal

The propeller-engine now supports pitch bends. We want to extend the py-propeller DSL to support this feature as well.

## propeller-engine pitch bends

Similar to notes, they can be set with the `pitch-bends` attribute in the tracks object.

```
  "tracks": [
    {
      "name": "lead",
      "channel": 1,
      "instrument": 0,
      "notes": [
        [0,    960, 60, 100],
        [960,  960, 60, 100]
      ],
      "pitch-bends": [
        [0,    8192],
        [120,  9192]
      ]
    }
  ]
```

See the following example: https://github.com/thomasvolk/propeller-engine/blob/main/examples/pitch_bend.json

Each pitch-bend event is a two-element integer array `[tick, value]`:

| Index | Field   | Type / Values    | Description                                                       |
| ----- | ------- | ---------------- | ----------------------------------------------------------------- |
| 0     | `tick`  | integer, ≥ 0     | Tick offset from the start of the loop; must be < `loop_duration` |
| 1     | `value` | integer, 0–16383 | 14-bit MIDI pitch-bend value; 8192 is center (no bend)            |

`pitch-bends` is optional and defaults to an empty list.

In this documentation you see how to set the values: https://github.com/thomasvolk/propeller-engine/blob/main/docs/json-socket-interface.md#pitch-bend-fields

## py-propeller pitch bends

A pitch bend can be set with the `PB` function. It takes a single argument, which is the pitch bend value. The value is a float between -1.0 and 1.0, where -1.0 is the maximum downward bend, 0.0 is no bend, and 1.0 is the maximum upward bend. The `PB` constant without an argument is equivalent to `PB(0.0)`.

In comparison to notes, `PB` has no length, so it is always applied to the next note. If you want to apply a pitch bend to a note, you have to place the `PB` function before the note.

```
p = project(
    bpm=120,
    time_signature=(4, 4),
    bars=1,
    tracks=[
        track(name="Piano",
              channel=2,
              instrument=0, 
              notes=[
                  C4(120),
                  PB(0.5),
                  D4(100),
                  PB,
                  E4(100),
                  F4]
        ),
    ],
)
p.play()

```
