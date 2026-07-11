from propeller.notes import Note

__all__: list[str] = []

_DRUM_SOUNDS: list[tuple[str, int]] = [
    ('Bass Drum 2', 35),
    ('Bass Drum 1', 36),
    ('Side Stick', 37),
    ('Snare Drum 1', 38),
    ('Hand Clap', 39),
    ('Snare Drum 2', 40),
    ('Low Tom 2', 41),
    ('Closed Hi-hat', 42),
    ('Low Tom 1', 43),
    ('Pedal Hi-hat', 44),
    ('Mid Tom 2', 45),
    ('Open Hi-hat', 46),
    ('Mid Tom 1', 47),
    ('High Tom 2', 48),
    ('Crash Cymbal 1', 49),
    ('High Tom 1', 50),
    ('Ride Cymbal 1', 51),
    ('Chinese Cymbal', 52),
    ('Ride Bell', 53),
    ('Tambourine', 54),
    ('Splash Cymbal', 55),
    ('Cowbell', 56),
    ('Crash Cymbal 2', 57),
    ('Vibra Slap', 58),
    ('Ride Cymbal 2', 59),
    ('High Bongo', 60),
    ('Low Bongo', 61),
    ('Mute High Conga', 62),
    ('Open High Conga', 63),
    ('Low Conga', 64),
    ('High Timbale', 65),
    ('Low Timbale', 66),
    ('High Agogo', 67),
    ('Low Agogo', 68),
    ('Cabasa', 69),
    ('Maracas', 70),
    ('Short Whistle', 71),
    ('Long Whistle', 72),
    ('Short Guiro', 73),
    ('Long Guiro', 74),
    ('Claves', 75),
    ('High Wood Block', 76),
    ('Low Wood Block', 77),
    ('Mute Cuica', 78),
    ('Open Cuica', 79),
    ('Mute Triangle', 80),
    ('Open Triangle', 81),
]

for _name, _pitch in _DRUM_SOUNDS:
    _const_name = _name.replace(' ', '').replace('-', '')
    globals()[_const_name] = Note(_pitch)
    __all__.append(_const_name)
