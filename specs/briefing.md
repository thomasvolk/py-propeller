Pitch bends `PB` can also make sense if they are only combined with rests (Z) in a lane.
All lanes will be combined together so that at the end pitch bands and notes are combined.
In the MIDI protocol a pitch bends affects all played notes of one instrument.

Here is an example:

```
from propeller.notes import D4, F4, A4, PB, Z
from propeller import project, track

p = project(
    bpm=80,
    time_signature=(4, 4),
    bars=2,
    tracks=[
        track(name="Lead",
              channel=1,
              instrument=0,
              notes=[
                [
                  PB(0.0),
                  D4 * 4,
                ],
                [
                  Z, F4 * 2
                ],
                [
                  Z * 2, A4 * 4
                ],
                [
                  Z,
                  PB(0.5)
                ]
              ]
        ),
    ],
)
p.play()
```

Current result: 

```
{"command": "create-project", "header": {"bpm": 80, "loop_duration": 3840}, "tracks": [{"name": "Lead", "channel": 1, "instrument": 0, "notes": [[0, 1920, 62, 100], [480, 960, 65, 100], [960, 1920, 69, 100]], "pitch-bends": [[0, 8192]]}]}
{"command": "loop-start"}
```

Expected result:

```
{"command": "create-project", "header": {"bpm": 80, "loop_duration": 3840}, "tracks": [{"name": "Lead", "channel": 1, "instrument": 0, "notes": [[0, 1920, 62, 100], [480, 960, 65, 100], [960, 1920, 69, 100]], "pitch-bends": [[0, 8192], [480, 12287]]}]}
{"command": "loop-start"}
```

Your task: fix the code so that the expected result will be produced.
