
I want to extend the language with a slide function. 
This function will be placed in its own module:
```python
from propeller.func import slide
```

With `slide`, you can create a series of Pitch Bend events combined with a series of notes so that it will sound like a slide.
This will slide from C4 to C5 in 0.1 steps, the slide is 4 quarter notes long (time signature is 4/4):
```python
              notes=
              [
                  slide(C4, C5, steps=0.1) * 4,
              ]
```

A Pitch Bend is affecting all notes of a track.
I Pitch Bend events calculated from multiple slides with the same point in time, will be consolidated. 
```python
              notes=[
                [
                  slide(C4, C5, steps=0.1) * 4,
                ],
                [
                  slide(E4, E5, steps=0.1) * 4, # This will only place the notes but, the PB events will be consoludated with the one above
                ],
              ]
```
