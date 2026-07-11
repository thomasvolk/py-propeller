import propeller.notes.drums as drums_module
from propeller.notes import Note
from propeller.composition import Track


GM1_DRUM_NOTE_NUMBERS = list(range(35, 82))
GM2_DRUM_NOTE_NUMBERS = list(range(27, 35)) + list(range(82, 88))


class TestDrumConstantCoverage:
    def test_module_defines_47_public_constants(self):
        assert len(drums_module.__all__) == 47

    def test_every_gm1_note_number_is_represented(self):
        pitches = {getattr(drums_module, name).pitch for name in drums_module.__all__}
        assert pitches == set(GM1_DRUM_NOTE_NUMBERS)

    def test_constants_are_note_instances(self):
        for name in drums_module.__all__:
            assert isinstance(getattr(drums_module, name), Note)


class TestDrumConstantNaming:
    def test_bass_drum_2_name_and_pitch(self):
        assert drums_module.BassDrum2 == Note(pitch=35)

    def test_bass_drum_1_name_and_pitch(self):
        assert drums_module.BassDrum1 == Note(pitch=36)

    def test_snare_drum_1_name_and_pitch(self):
        assert drums_module.SnareDrum1 == Note(pitch=38)

    def test_hand_clap_name_and_pitch(self):
        assert drums_module.HandClap == Note(pitch=39)

    def test_high_wood_block_name_and_pitch(self):
        assert drums_module.HighWoodBlock == Note(pitch=76)

    def test_open_triangle_name_and_pitch(self):
        assert drums_module.OpenTriangle == Note(pitch=81)


class TestHyphenatedDrumNames:
    def test_closed_hihat_name_and_pitch(self):
        assert drums_module.ClosedHihat == Note(pitch=42)

    def test_pedal_hihat_name_and_pitch(self):
        assert drums_module.PedalHihat == Note(pitch=44)

    def test_open_hihat_name_and_pitch(self):
        assert drums_module.OpenHihat == Note(pitch=46)


class TestGM2SoundsAreExcluded:
    def test_no_public_constant_resolves_to_a_gm2_note_number(self):
        pitches = {getattr(drums_module, name).pitch for name in drums_module.__all__}
        assert pitches.isdisjoint(GM2_DRUM_NOTE_NUMBERS)

    def test_known_gm2_only_names_are_not_defined(self):
        for name in ('HighQ', 'Slap', 'Sticks', 'Shaker', 'JingleBell', 'Castanets'):
            assert not hasattr(drums_module, name)


class TestDrumConstantsUsableInTrack:
    def test_snare_drum_1_is_a_note_instance(self):
        assert isinstance(drums_module.SnareDrum1, Note)

    def test_drum_constant_can_be_placed_in_a_track_with_pitch_constants(self):
        from propeller.notes import C4
        track = Track(
            name='Drums',
            channel=10,
            instrument=0,
            notes=[C4, drums_module.SnareDrum1, drums_module.ClosedHihat],
        )
        assert track.notes[1] is drums_module.SnareDrum1


class TestDrumConstantsAllExport:
    def test_all_contains_every_public_constant_and_nothing_else(self):
        module_public_names = {
            name for name in vars(drums_module)
            if not name.startswith('_') and isinstance(getattr(drums_module, name), Note)
        }
        assert set(drums_module.__all__) == module_public_names
