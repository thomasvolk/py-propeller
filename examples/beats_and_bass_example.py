from propeller.notes import C4, D4, E4, F2, D3, C3, Z
from propeller import project, track
from propeller import loop

p = loop.get_position()

# Note definitions for Korg Volca Drum
BD = C4
HH = D4
SN = E4
R = Z

if p.loop_count % 2 == 0:
    hh = []
else:
    hh = [
           HH * 0.5, HH * 0.5,
           HH * 0.5, HH * 0.5,
           HH * 0.5, HH * 0.5,
           HH * 0.5, HH * 0.5,
          ] * 2

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
                  BD *  1,
              ],
              hh
        ]),
        track(name="Bass",
              channel=4,
              instrument=0,
              notes=[
                  D3(120),
                  C3(100),
                  D3(100),
                  F2 * 1.5,
                  R * 3.5]
        ),
    ],
)
p.play()
