from propeller.notes.drums import BassDrum1, SnareDrum1, ClosedHihat, ClosedHihat
from propeller.notes import C4, D4, E4, Z
from propeller import project, track
from propeller import status

s = status.get_status()
if s.midi_port_name is not None:
    # for volca drum in my personal setup
    BassDrum1 = C4
    SnareDrum1 = E4
    ClosedHihat = D4

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
                  BassDrum1 *  1,
                  SnareDrum1 *  1.5,
                  BassDrum1 *  0.5,
                  SnareDrum1 *  0.5,
                  BassDrum1 *  0.5,
                  BassDrum1 *  1,
                  SnareDrum1 *  1.5,
                  BassDrum1 *  0.5,
                  SnareDrum1 *  1,
              ],
              [
               Z * 0.5, ClosedHihat * 0.5,
               Z * 0.5, ClosedHihat * 0.5,
               ClosedHihat * 0.5, ClosedHihat * 0.5,
               ClosedHihat * 0.5, ClosedHihat * 0.5,
              ] * 2
        ]),
    ],
)
p.play()
