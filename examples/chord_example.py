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
            [
                C4() * 2,
            ],
            [
                E4() * 2,
            ],
            [
                G4() * 2,
            ]
        ])
    ],
)
p.play()
