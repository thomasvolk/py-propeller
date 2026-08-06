from propeller.notes import C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F5, Gs4, Ef5, Z
from propeller import project, track

# Beethoven - Für Elise (WoO 59), main theme
# 3/4 time, 1 beat = quarter note; eighth notes use *0.5
p = project(
    bpm=100,
    time_signature=(3, 4),
    bars=8,
    tracks=[
        track(
            name="Piano",
            channel=1,
            instrument=0,
            notes=[
                # Opening motif
                E5*0.5, Ef5*0.5, E5*0.5, Ef5*0.5, E5*0.5, B4*0.5,
                D5*0.5, C5*0.5, A4*1.0,
                # First interlude
                Z*0.5, C4*0.5, E4*0.5, A4*0.5, B4*1.0,
                Z*0.5, E4*0.5, Gs4*0.5, B4*0.5, C5*1.0,
                # Repeat opening motif
                Z*0.5, E5*0.5, Ef5*0.5, E5*0.5, Ef5*0.5, E5*0.5,
                B4*0.5, D5*0.5, C5*0.5, A4*1.0,
                # Modified ending
                Z*0.5, C4*0.5, E4*0.5, A4*0.5, B4*1.0,
                Z*0.5, E4*0.5, C5*0.5, B4*0.5, A4*1.5,
                Z*1.5,
            ],
        ),
    ],
)
p.play()
