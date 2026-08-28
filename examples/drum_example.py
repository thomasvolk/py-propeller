from propeller.notes.drums import BassDrum1, SnareDrum1, ClosedHihat, OpenHihat
from propeller.notes import C4, D4, E4
from propeller import project, track
from propeller import status

s = status.get_status()
if s.midi_port_name == 'USB MIDI Interface':
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
