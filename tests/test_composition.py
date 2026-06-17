import dataclasses

import pytest

from propeller.errors import PropellerError, PropellerValidationError
from propeller.notes import C4, D4, E4, F4


class TestTrackConstruction:
    def test_attributes(self):
        from propeller.composition import Track
        t = Track(name="Piano", channel=2, instrument=0, notes=[C4, D4, E4, F4])
        assert t.name == "Piano"
        assert t.channel == 2
        assert t.instrument == 0
        assert len(t.notes) == 4

    def test_repr_is_non_empty(self):
        from propeller.composition import Track
        t = Track(name="Piano", channel=1, instrument=0, notes=[C4])
        assert repr(t)

    def test_empty_notes(self):
        from propeller.composition import Track
        t = Track(name="Drums", channel=10, instrument=0, notes=[])
        assert t.notes == []

    def test_notes_index_access(self):
        from propeller.composition import Track
        t = Track(name="Bass", channel=1, instrument=32, notes=[C4])
        assert t.notes[0] is C4


class TestTrackChannelValidation:
    def test_channel_too_high_raises(self):
        from propeller.composition import Track
        with pytest.raises(PropellerValidationError):
            Track(name="x", channel=17, instrument=0, notes=[])

    def test_channel_negative_raises(self):
        from propeller.composition import Track
        with pytest.raises(PropellerValidationError):
            Track(name="x", channel=-1, instrument=0, notes=[])

    def test_channel_zero_raises(self):
        from propeller.composition import Track
        with pytest.raises(PropellerValidationError):
            Track(name="x", channel=0, instrument=0, notes=[])

    def test_channel_one_is_valid(self):
        from propeller.composition import Track
        t = Track(name="x", channel=1, instrument=0, notes=[])
        assert t.channel == 1

    def test_channel_sixteen_is_valid(self):
        from propeller.composition import Track
        t = Track(name="x", channel=16, instrument=0, notes=[])
        assert t.channel == 16

    def test_channel_error_is_propeller_error_subclass(self):
        from propeller.composition import Track
        with pytest.raises(PropellerError) as exc_info:
            Track(name="x", channel=17, instrument=0, notes=[])
        assert isinstance(exc_info.value, PropellerValidationError)
        assert str(exc_info.value)


class TestTrackInstrumentValidation:
    def test_instrument_too_high_raises(self):
        from propeller.composition import Track
        with pytest.raises(PropellerValidationError):
            Track(name="x", channel=1, instrument=128, notes=[])

    def test_instrument_negative_raises(self):
        from propeller.composition import Track
        with pytest.raises(PropellerValidationError):
            Track(name="x", channel=1, instrument=-1, notes=[])

    def test_instrument_zero_is_valid(self):
        from propeller.composition import Track
        t = Track(name="x", channel=1, instrument=0, notes=[])
        assert t.instrument == 0

    def test_instrument_127_is_valid(self):
        from propeller.composition import Track
        t = Track(name="x", channel=1, instrument=127, notes=[])
        assert t.instrument == 127


class TestTrackNotesTypeValidation:
    def test_invalid_element_raises_with_position(self):
        from propeller.composition import Track
        with pytest.raises(PropellerValidationError) as exc_info:
            Track(name="x", channel=1, instrument=0, notes=[C4, "bad", D4])
        assert "2" in str(exc_info.value)

    def test_invalid_element_at_first_position(self):
        from propeller.composition import Track
        with pytest.raises(PropellerValidationError) as exc_info:
            Track(name="x", channel=1, instrument=0, notes=[42])
        assert "1" in str(exc_info.value)


class TestTrackNameValidation:
    def test_empty_name_raises_validation_error(self):
        from propeller.composition import Track
        with pytest.raises(PropellerValidationError) as exc_info:
            Track(name="", channel=1, instrument=0, notes=[])
        assert 'name' in str(exc_info.value)

    def test_non_empty_name_succeeds(self):
        from propeller.composition import Track
        t = Track(name="Piano", channel=1, instrument=0, notes=[])
        assert t.name == "Piano"


class TestTrackNoteVelocityValidation:
    def test_note_with_velocity_200_at_position_1_raises(self):
        from propeller.composition import Track
        from propeller.notes import Note
        with pytest.raises(PropellerValidationError) as exc_info:
            Track(name="X", channel=1, instrument=0, notes=[Note(60, 1.0, 200)])
        assert 'position 1' in str(exc_info.value)

    def test_note_with_velocity_200_at_position_2_raises(self):
        from propeller.composition import Track
        from propeller.notes import C4, Note
        with pytest.raises(PropellerValidationError) as exc_info:
            Track(name="X", channel=1, instrument=0, notes=[C4, Note(60, 1.0, 200)])
        assert 'position 2' in str(exc_info.value)

    def test_rest_at_any_position_does_not_trigger_velocity_check(self):
        from propeller.composition import Track
        from propeller.notes import Rest
        t = Track(name="X", channel=1, instrument=0, notes=[Rest(), Rest()])
        assert len(t.notes) == 2

    def test_valid_notes_succeed(self):
        from propeller.composition import Track
        from propeller.notes import C4, D4
        t = Track(name="X", channel=1, instrument=0, notes=[C4, D4])
        assert len(t.notes) == 2


class TestTrackImmutability:
    def test_name_mutation_raises(self):
        from propeller.composition import Track
        t = Track(name="Piano", channel=1, instrument=0, notes=[])
        with pytest.raises(dataclasses.FrozenInstanceError):
            t.name = "Other"


class TestProjectConstruction:
    def test_attributes(self):
        from propeller.composition import Track, Project
        t = Track(name="Piano", channel=1, instrument=0, notes=[C4])
        p = Project(bpm=120, time_signature=(4, 4), bars=2, tracks=[t])
        assert p.bpm == 120
        assert p.time_signature == (4, 4)
        assert p.bars == 2
        assert p.tracks == [t]

    def test_track_name_accessible(self):
        from propeller.composition import Track, Project
        t = Track(name="Piano", channel=1, instrument=0, notes=[C4])
        p = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        assert p.tracks[0].name == "Piano"

    def test_repr_is_non_empty(self):
        from propeller.composition import Project
        p = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[])
        assert repr(p)

    def test_empty_tracks(self):
        from propeller.composition import Project
        p = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[])
        assert p.tracks == []


class TestProjectBpmValidation:
    def test_bpm_zero_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError):
            Project(bpm=0, time_signature=(4, 4), bars=1, tracks=[])

    def test_bpm_negative_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError):
            Project(bpm=-1, time_signature=(4, 4), bars=1, tracks=[])

    def test_bpm_positive_is_valid(self):
        from propeller.composition import Project
        p = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[])
        assert p.bpm == 120


class TestProjectBarsValidation:
    def test_bars_zero_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError):
            Project(bpm=120, time_signature=(4, 4), bars=0, tracks=[])

    def test_bars_negative_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError):
            Project(bpm=120, time_signature=(4, 4), bars=-1, tracks=[])

    def test_bars_one_is_valid(self):
        from propeller.composition import Project
        p = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[])
        assert p.bars == 1

    def test_bars_two_is_valid(self):
        from propeller.composition import Project
        p = Project(bpm=120, time_signature=(4, 4), bars=2, tracks=[])
        assert p.bars == 2


class TestProjectTimeSignatureValidation:
    def test_zero_numerator_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError) as exc_info:
            Project(bpm=120, bars=2, time_signature=(0, 4), tracks=[])
        assert 'time_signature' in str(exc_info.value)

    def test_negative_denominator_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError) as exc_info:
            Project(bpm=120, bars=2, time_signature=(4, -1), tracks=[])
        assert 'time_signature' in str(exc_info.value)

    def test_single_element_tuple_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError) as exc_info:
            Project(bpm=120, bars=2, time_signature=(4,), tracks=[])
        assert 'time_signature' in str(exc_info.value)

    def test_string_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError) as exc_info:
            Project(bpm=120, bars=2, time_signature="4/4", tracks=[])
        assert 'time_signature' in str(exc_info.value)

    def test_zero_denominator_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError) as exc_info:
            Project(bpm=120, bars=2, time_signature=(4, 0), tracks=[])
        assert 'time_signature' in str(exc_info.value)

    def test_bool_element_raises(self):
        from propeller.composition import Project
        with pytest.raises(PropellerValidationError) as exc_info:
            Project(bpm=120, bars=2, time_signature=(True, 4), tracks=[])
        assert 'time_signature' in str(exc_info.value)

    def test_four_four_succeeds(self):
        from propeller.composition import Project
        p = Project(bpm=120, bars=2, time_signature=(4, 4), tracks=[])
        assert p.time_signature == (4, 4)

    def test_three_eight_succeeds(self):
        from propeller.composition import Project
        p = Project(bpm=120, bars=2, time_signature=(3, 8), tracks=[])
        assert p.time_signature == (3, 8)


class TestProjectImmutability:
    def test_bpm_mutation_raises(self):
        from propeller.composition import Project
        p = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[])
        with pytest.raises(dataclasses.FrozenInstanceError):
            p.bpm = 200


class TestTopLevelImport:
    def test_import_track_and_project(self):
        from propeller import project, track
        assert callable(track)
        assert callable(project)

    def test_end_to_end_via_top_level(self):
        from propeller import project, track
        t = track(name="Guitar", channel=1, instrument=25, notes=[C4, D4])
        p = project(bpm=140, time_signature=(4, 4), bars=4, tracks=[t])
        assert p.bpm == 140
        assert p.tracks[0].name == "Guitar"
