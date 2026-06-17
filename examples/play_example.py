from propeller.notes import *
from propeller import project, track

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
                  D4(100),
                  E4(100),
                  F4]
        ),
    ],
)
p.play()
