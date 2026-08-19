from propeller.notes import C4, E4, Slide
from propeller.notes.Slide import to
from propeller import project, track

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
    ],
)
p.play()
