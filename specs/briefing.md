
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

### Overlapping notes

The propeller engine supports playing overlapping notes by setting the start-tick for every note explicitly.
py-propeller calculates the start-tick of a note by summarizing the duration of its predecessor.
Nevertheless, to support overlapping of notes the py-propeller uses a trick by allowing multiple lanes per track.
- Lanes are organized as list of lists `notes = [ [C4], [E4] ]`.
- This feature is optional: If `notes` is a flat list, it will be handled as one lane.
- The start-tick of a note will be calculated in every lane independently.
- If all notes have calculates start-ticks the lanes will be flatten to one result list - py-propeller will detect this automatically.

This is an example for a c major chord. The start-tick of all three notes will be 0.
```python
    track(
        name = "Piano",
        channel = 2,
        instrument = 0,
        notes = [
            [
                C4(),
            ],
            [
                E4(), 
            ],
            [
                G4(), 
            ]
        ]
    )
```


## Uploading to the Engine

When you call the `.play()` method on the project, it will transform the project to the propeller JSON format and upload it to the engine via socket. The engine will then start playing the project immediately.

```
python my_project.py
```

By default the execution of the script will block until you stop it, so you can keep it running in the background while you edit the file.

### Non-blocking mode

The script can also be executed in non-blocking mode by using the state `-s` parameter.
This parameter has two values:
- active: create or modify a project and start the loop
- inactive: stop the loop

The state parameter has no effect on the dry run mode

**What non-blocking means**: When calling the script with the `-s` parameter, the script sends its commands to the propeller engine and exits immediately!

#### State active:

If no project is present, the propellers `create-project` command will be executed and the loop will be started.
If a project is present, the propellers `modify-project` command will be executed and the loop will be started.

Example:
```
python my_project.py -s active
```

If a project is present can be find out with the propellers `status` command.
Response:

    {"status":"ok","project_present":true,...}

#### State inactive:

This state sends a `loop-stop` command to the propeller engine.

Example:
```
python my_project.py -s inactive
```

## Dry run

For debugging purpose a dry run is possible by adding the parameter `-n`.
Instead of communicating to the socked, all JSON data will be printed to the console. 
In dry run mode the `.play()` is non blocking.

