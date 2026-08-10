
I want to extend the language with a probability function. 
This function will be placed in its own module:
```python
from propeller.func import probability
```

With `probability`, you can decorate a note with a probability value.

In this example the `SnareDrum1` note will be played with a probability of 0.5, and if it is not played, it will be replaced with a `Z` (rest) note.
The length of the note will be halved, so it will only play for half the duration of a normal `SnareDrum1` or the `Z` note.
If the last parameter is not specified, the default replacement will be a `Z` note.
```python
              notes=
              [
                  BassDrum1(110),
                  SnareDrum1(100),
                  BassDrum1(110),
                  SnareDrum1(100) * 0.5,
                  probability(0.5, SnareDrum1, replacement=Z) * 0.5,
              ]
```
