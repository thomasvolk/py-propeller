from propeller.notes import C4, PB
from propeller import project, track

p = project(
    bpm=80,
    time_signature=(4, 4),
    bars=2,
    tracks=[
        track(name="Lead",
              channel=1,
              instrument=0,
              notes=[
                  PB(0.0),   C4(100),
                  PB(0.25),  C4(100),
                  PB(0.5),   C4(100),
                  PB(0.75),  C4(100),
                  PB(1.0),   C4(100),
                  PB(-0.25), C4(100),
                  PB(-0.5),  C4(100),
                  PB(-0.75),   C4(100),
              ]
        ),
    ],
)
p.play()
