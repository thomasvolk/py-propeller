# Run this with the py-propeller watch script (`py-propeller examples/probability_example.py`).
# probability() is only rolled once, when this module is executed, so it needs the watcher's
# periodic reload to re-roll on every tick — running it once via plain `python` freezes the
# outcome for the whole playback.
from propeller.notes.drums import BassDrum1, SnareDrum1, HandClap
from propeller.func import probability
from propeller import project, track

p = project(
    bpm=100,
    time_signature=(4, 4),
    bars=1,
    tracks=[
        track(name="Drums",
              channel=10,
              instrument=0,
              notes=[
                  BassDrum1(110),
                  probability(0.5, SnareDrum1, replacement=HandClap),
                  BassDrum1(110),
                  SnareDrum1(100) * 0.5,
                  probability(0.5, SnareDrum1) * 0.5, # default replacement is Z
              ]
        ),
    ],
)
p.play()
