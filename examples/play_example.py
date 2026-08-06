from propeller.notes import C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F5, G5, A5, B5
from propeller import project, track

p = project(
    bpm=120,
    time_signature=(8, 8),
    bars=2,
    tracks=[
        track(name="Piano",
              channel=2,
              instrument=0,
              notes=[
                [
                  C4,
                  C5,
                  E4,
                  E5,
                  D4,
                  D5,
                  E4,
                  E5,

                  C4,
                  C5,
                  E4,
                  E5,
                  D4,
                  D5,
                  C4,
                  C5,

              ],
            ]
        ),
    ],
)
p.play()
