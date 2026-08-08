from propeller.notes import C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F5, G5, A5, B5, G6, F6, PB
from propeller import project, track

# Surge XT - Slowboat -> Basses -> Bass FX 1

p = project(
    bpm=120,
    time_signature=(8, 8),
    bars=2,
    tracks=[
        track(name="Bass",
              channel=4,
              instrument=0,
              notes=[
                [
                  PB(0),
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
        track(name="Lead",
              channel=2,
              instrument=0,
              notes=[
                [
                  G6 * 8,

                  F6 * 8,

              ],
            ]
        ),
    ],
)
p.play()
