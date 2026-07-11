from propeller.notes.drums import BassDrum1, SnareDrum1, ClosedHihat, OpenHihat
from propeller import project, track

p = project(
    bpm=100,
    time_signature=(4, 4),
    bars=2,
    tracks=[
        track(name="Drums",
              channel=10,
              instrument=0,
              notes=[
              [
                  BassDrum1(110),
                  SnareDrum1(100),
                  BassDrum1(110),
                  SnareDrum1(100),
              ] * 2,
              [
                  ClosedHihat(80) * 0.5, ClosedHihat(80) * 0.5,
                  ClosedHihat(80) * 0.5, ClosedHihat(80) * 0.5,
                  ClosedHihat(80) * 0.5, ClosedHihat(80) * 0.5,
                  ClosedHihat(80) * 0.5, OpenHihat(90)   * 0.5,
              ] * 2
        ]),
    ],
)
p.play()
