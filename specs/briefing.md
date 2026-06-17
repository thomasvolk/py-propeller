
This is a client for the propeller-engine. I is a simple python library wich works as internal DSL.
This DSL has the goal to present a propeller-engine project in a human readable form.

## Features

- transform the DSL it to the propeller JSON format - please load the spec: https://github.com/thomasvolk/propeller-engine/blob/main/docs/json-socket-interface.md
- upload the JSON to the engine via socket

## DSL Draft

```python
from propeller.notes import *
from propeller import project, track

project(
  bpm = 120,
  time_signature = (4, 4),
  bars = 2,
  tracks = [
    track(
        name = "Piano",
        channel = 2,
        instrument = 0,
        notes = [
          C4(120) *   2,
          D4()    * 0.5, 
          E4()    * 0.5, 
          F4(),
          E4(120) *   2, 
          Ds4()   * 0.5, 
          Ef4()   * 0.5, 
          Cs4()   *   1
        ]
    )
  ]
).start()
```

- C4(120) is the middle c (midi note number 60) the number is the octave velocity is 120.
- Cs4() is the c sharp in the 4th octave (midi note number 61) velocity is 100 (default)
- Ef4() is the e flat in the 4th octave (midi note number 63) velocity is 100 (default)
- all notes are predefined as constants in the `propeller.notes` module
- C4() * 2 means that the note C4 should be played for 2 beats, D4 * 0.5 means that the note D4 should be played for half a beat, etc.
- Z or z is for rest
- Z * 2 is a two beat rest
- the velocity is by default 100
- the velocity value can be be set a parameter of the note, e.g. C4(120) means that the note C4 should be played with a velocity of 120

## Uploading to the Engine

When you call the `.play()` method on the project, it will transform the project to the propeller JSON format and upload it to the engine via socket. The engine will then start playing the project immediately.

```
python my_project.py
```

The execution of the script will block until you stop it, so you can keep it running in the background while you edit the file.

```
python my_project.py
```

## Dry run

For debugging purpose a dry run is possible by adding the parameter `-n`.
Instead of communicating to the socked, all JSON data will be printed to the console. 
In dry run mode the `.play()` is non blocking.

