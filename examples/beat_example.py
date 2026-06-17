from propeller.notes import *
from propeller import project, track

BD = C4
SN = E4

p = project(
    bpm=100,
    time_signature=(4, 4),
    bars=1,
    tracks=[
        track(name="Drums",
              channel=16,
              instrument=0,
              notes=[
                  BD *  1,
                  SN *  1.5,
                  BD *  0.5,
                  SN *  0.5,
                  BD *  0.5
        ]),
    ],
)
p.play()
