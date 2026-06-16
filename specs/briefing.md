
This is a client for the propeller-engine. I is a simple python library wich works as internal DSL.
This DSL has the goal to present a propeller-engine project in a human readable form.

## Features

- transform the DSL it to the propeller JSON format (see: https://github.com/thomasvolk/propeller-engine/blob/main/docs/json-socket-interface.md)
- upload the JSON to the engine via socket

## DSL Draft

```python
from propeller.notes import *
from propeller import project, track

project(
  bpm = 120,
  time_signature = (4, 4)
  tracks = [
    track(
        name = "Piano",
        channel = 2,
        instrument = 0,
        notes = [
          [ C4 * 2 + 30, D4 * 0.5, E4 * 0.5, F4],  
          [ E4 * 2 + 30, Ds4 * 0.5, Ef4 * 0.5, Cs4],  
        ]
    )
  ]
).play()
```

- C4 is the middle c (midi note number 60) the number is the octave.
- Cs4 is the c sharp in the 4th octave (midi note number 61)
- Ef4 is the e flat in the 4th octave (midi note number 63)
- all notes are predefined as constants in the `propeller.notes` module
- C4 * 2 means that the note C4 should be played for 2 beats, D4 * 0.5 means that the note D4 should be played for half a beat, etc.
- Z or z is for rest
- Z * 2 is a two beat rest
- the velocity is by default 100
- the velocity default value can be increased and decreased by the '+' and '-' operators. Examples: C4 - 20, A4 * 8 + 5, (E3 + 30) * 4 

## Uploading to the Engine

When you call the `.play()` method on the project, it will transform the project to the propeller JSON format and upload it to the engine via socket. The engine will then start playing the project immediately.

```
python my_project.py
```

The execution of the script will block until you stop it, so you can keep it running in the background while you edit the file.

```
python my_project.py
```
