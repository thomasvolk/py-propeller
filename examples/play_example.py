from propeller.notes import *
from propeller import project, track

p = project(
    bpm=120,
    time_signature=(4, 4),
    bars=1,
    tracks=[
        track(name="Piano", channel=0, instrument=0, notes=[C4, D4, E4, F4]),
    ],
)
p.play()
