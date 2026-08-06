from propeller.notes import C4, D4, E4, Z
from propeller import project, track

BD = C4
HH = D4
SN = E4
R = Z

p = project(
    bpm=100,
    time_signature=(4, 4),
    bars=2,
    tracks=[
        track(name="Drums",
              channel=16,
              instrument=0,
              notes=[
              [
                  BD *  1,
                  SN *  1.5,
                  BD *  0.5,
                  SN *  0.5,
                  BD *  0.5,
                  BD *  1,
                  SN *  1.5,
                  BD *  0.5,
                  SN *  1,
              ],
              [
               R * 0.5, HH * 0.5,
               R * 0.5, HH * 0.5,
               HH * 0.5, HH * 0.5,
               HH * 0.5, HH * 0.5,
              ] * 2
        ]),
    ],
)
p.play()
