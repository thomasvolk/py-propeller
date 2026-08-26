from propeller.notes import C4, D4, E4, F4, Slide
from propeller.notes.Slide import cos, gauss, sin, to
from propeller import project, track


def vibrato(ctx):
    # a custom curve: progress -> pitch-bend value, same shape as sin/cos/gauss
    import math
    return 0.1 * math.sin(ctx * 16 * math.pi)


p = project(
    bpm=260,
    time_signature=(4, 4),
    bars=1,
    tracks=[
        track(name="Lead",
              channel=1,
              instrument=0,
              notes=[
                  [
                      Slide(C4, to(1.0, steps=0.01)) * 4,
                  ],
                  [
                      # Two concurrent slides on the same track sharing the
                      # same target/steps: their pitch-bend events are
                      # consolidated instead of conflicting.
                      Slide(E4, to(1.0, steps=0.01)) * 4,
                  ],
              ]
        ),
        track(name="Effects",
              channel=2,
              instrument=0,
              notes=[
                  Slide(C4, sin(amp=1, period=2, y_offset=0)) * 4,
                  Slide(D4, cos(amp=1, period=2, y_offset=0)) * 4,
                  Slide(E4, gauss(u=0, o=1)) * 4,
                  Slide(F4, vibrato) * 4,
              ]
        ),
    ],
)
p.play()
