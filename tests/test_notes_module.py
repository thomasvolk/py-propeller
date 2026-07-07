import pytest
import propeller.notes as notes_module
from propeller.notes import Note, Rest


class TestZandz:
    def test_Z_is_rest(self):
        from propeller.notes import Z
        assert isinstance(Z, Rest)

    def test_z_is_rest(self):
        from propeller.notes import z
        assert isinstance(z, Rest)

    def test_Z_default_duration(self):
        from propeller.notes import Z
        assert Z.duration == 1.0

    def test_z_default_duration(self):
        from propeller.notes import z
        assert z.duration == 1.0

    def test_Z_mul(self):
        from propeller.notes import Z
        result = Z * 2
        assert result.duration == 2.0
        assert Z.duration == 1.0

    def test_z_mul(self):
        from propeller.notes import z
        result = z * 2
        assert result.duration == 2.0
        assert z.duration == 1.0


class TestNoteConstants:
    def test_C4_pitch(self):
        from propeller.notes import C4
        assert C4.pitch == 60

    def test_Cs4_pitch(self):
        from propeller.notes import Cs4
        assert Cs4.pitch == 61

    def test_Ef4_pitch(self):
        from propeller.notes import Ef4
        assert Ef4.pitch == 63

    def test_Df4_is_enharmonic_with_Cs4(self):
        from propeller.notes import Df4, Cs4
        assert Df4.pitch == 61
        assert Df4.pitch == Cs4.pitch

    def test_C0_pitch(self):
        from propeller.notes import C0
        assert C0.pitch == 12

    def test_C8_pitch(self):
        from propeller.notes import C8
        assert C8.pitch == 108

    def test_every_pitch_in_octaves_0_to_8_reachable(self):
        all_pitches = {
            getattr(notes_module, name).pitch
            for name in notes_module.__all__
            if isinstance(getattr(notes_module, name), Note)
        }
        # C0=12 through C8=108; all 12 semitones per octave
        for octave in range(9):
            for semitone in range(12):
                pitch = (octave + 1) * 12 + semitone
                assert pitch in all_pitches, f'pitch {pitch} missing'


class TestStarImport:
    def test_star_import_includes_C4(self):
        assert 'C4' in notes_module.__all__

    def test_star_import_includes_Cs4(self):
        assert 'Cs4' in notes_module.__all__

    def test_star_import_includes_Z(self):
        assert 'Z' in notes_module.__all__

    def test_star_import_includes_z(self):
        assert 'z' in notes_module.__all__

    def test_star_import_excludes_Note(self):
        assert 'Note' not in notes_module.__all__

    def test_star_import_excludes_Rest(self):
        assert 'Rest' not in notes_module.__all__

    def test_star_import_excludes_internal_helpers(self):
        for name in notes_module.__all__:
            assert not name.startswith('_'), f'internal name {name!r} in __all__'

    def test_all_exported_names_are_note_rest_or_pitch_bend(self):
        from propeller.notes import PitchBend
        for name in notes_module.__all__:
            obj = getattr(notes_module, name)
            assert isinstance(obj, (Note, Rest, PitchBend)), (
                f'{name!r} in __all__ is not a Note, Rest, or PitchBend'
            )
