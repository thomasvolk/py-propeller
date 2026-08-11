
I want to extend the language with a Slide note. 
```python
from propeller.notes import Slide
```

With `Slide`, you can create a series of Pitch Bend events combined with a series of notes so that it will sound like a slide.
This will slide from C4 to C5 in 0.1 steps, the slide is 4 quarter notes long (time signature is 4/4):
```python
              notes=
              [
                  Slide(C4, C5, steps=0.1) * 4,
              ]
```
The algorithm:
* We assume that the standard MIDI device has a Pitch Bend from -1 to +1 note - this is the defualt
* Calculate the one tone intervals between the start (C4) and the end note (C5) - C4, D4, E4, Fs4, Gs4, As4, C5
* Here we have 6 intervals - every interval must have the same length: here a 1/6 note
* We start with the first note C4 and slide the interval of 1/6 note with a series of Pitch Bends (PB) to D4 - PB length = (1/6) * steps 

`Slide` is a note because it must directly produce the entries in the propeller json.

A Pitch Bend is affecting all notes of a track.
I Pitch Bend events calculated from multiple slides with the same point in time, will be consolidated. 
```python
              notes=[
                [
                  Slide(C4, C5, steps=0.1) * 4,
                ],
                [
                  Slide(E4, E5, steps=0.1) * 4, # This will only place the notes but, the PB events will be consoludated with the one above
                ],
              ]
```
