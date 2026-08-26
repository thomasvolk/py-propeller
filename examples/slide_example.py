from propeller.notes import C4, D4, E4, F4, G4, Slide
from propeller.notes.Slide import cos, gauss, sin, to
from propeller import project, track


def vibrato(ctx):
    # a custom curve: progress -> pitch-bend value, same shape as sin/cos/gauss
    import math
    return 0.1 * math.sin(ctx * 16 * math.pi)


p = project(
    bpm=120,
    time_signature=(4, 4),
    bars=5,
    tracks=[
        track(name="Lead",
              channel=1,
              instrument=0,
              notes=[
                  [
                      Slide(C4, to(1.0, steps=0.01)) * 4,
                      Slide(D4, sin(amp=1, period=2, y_offset=0)) * 4,
                      Slide(E4, cos(amp=1, period=2, y_offset=0)) * 4,
                      Slide(F4, gauss(u=0, o=1)) * 4,
                      Slide(G4, vibrato) * 4,
                  ],
              ]
        ),
    ],
)
p.play()
