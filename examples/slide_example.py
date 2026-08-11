from propeller.notes import C4, C5, E4, E5, Slide
from propeller import project, track

p = project(
    bpm=100,
    time_signature=(4, 4),
    bars=2,
    tracks=[
        track(name="Lead",
              channel=1,
              instrument=0,
              notes=[
                  [
                      Slide(C4, C5, steps=0.1) * 4,
                  ],
                  [
                      # Two concurrent slides on the same track: their pitch-bend
                      # events are consolidated instead of conflicting.
                      #Slide(E4, E5, steps=0.1) * 4,
                  ],
              ]
        ),
    ],
)
p.play()
