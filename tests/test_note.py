import pytest
from propeller.errors import PropellerValidationError
from propeller.notes import Note, Rest


class TestNoteConstruction:
    def test_pitch_field(self):
        n = Note(60)
        assert n.pitch == 60

    def test_default_duration(self):
        n = Note(60)
        assert n.duration == 1.0

    def test_default_velocity(self):
        n = Note(60)
        assert n.velocity == 100

    def test_fields_are_readable(self):
        n = Note(pitch=48, duration=2.0, velocity=80)
        assert n.pitch == 48
        assert n.duration == 2.0
        assert n.velocity == 80

    def test_immutable(self):
        n = Note(60)
        with pytest.raises(Exception):
            n.pitch = 61


class TestNoteMul:
    def test_mul_returns_new_note_with_updated_duration(self):
        n = Note(60)
        result = n * 2
        assert result.duration == 2.0

    def test_mul_preserves_original(self):
        n = Note(60)
        _ = n * 2
        assert n.duration == 1.0

    def test_mul_preserves_pitch(self):
        n = Note(60)
        result = n * 3
        assert result.pitch == 60

    def test_mul_preserves_velocity(self):
        n = Note(60, velocity=80)
        result = n * 3
        assert result.velocity == 80

    def test_mul_float_duration(self):
        n = Note(60)
        result = n * 0.5
        assert result.duration == 0.5

    def test_mul_zero_raises_validation_error(self):
        n = Note(60)
        with pytest.raises(PropellerValidationError) as exc_info:
            n * 0
        assert 'duration' in str(exc_info.value)

    def test_mul_negative_raises_validation_error(self):
        n = Note(60)
        with pytest.raises(PropellerValidationError) as exc_info:
            n * -1
        assert 'duration' in str(exc_info.value)

    def test_mul_no_position_context_in_message(self):
        n = Note(60)
        with pytest.raises(PropellerValidationError) as exc_info:
            n * 0
        msg = str(exc_info.value)
        assert 'position' not in msg
        assert 'bar' not in msg

    def test_mul_half_beat_succeeds(self):
        n = Note(60)
        result = n * 0.5
        assert result.duration == 0.5

    def test_mul_two_beats_succeeds(self):
        n = Note(60)
        result = n * 2
        assert result.duration == 2.0


class TestNoteCall:
    def test_call_with_velocity_returns_new_note(self):
        n = Note(60)
        result = n(120)
        assert result.velocity == 120

    def test_call_preserves_original(self):
        n = Note(60)
        _ = n(120)
        assert n.velocity == 100

    def test_call_no_args_returns_default_velocity(self):
        n = Note(60)
        result = n()
        assert result.velocity == 100

    def test_call_preserves_pitch(self):
        n = Note(60)
        result = n(120)
        assert result.pitch == 60

    def test_call_preserves_duration(self):
        n = Note(60, duration=2.0)
        result = n(120)
        assert result.duration == 2.0

    def test_call_velocity_upper_boundary(self):
        n = Note(60)
        result = n(127)
        assert result.velocity == 127

    def test_call_velocity_lower_boundary(self):
        n = Note(60)
        result = n(0)
        assert result.velocity == 0

    def test_call_velocity_too_high_raises(self):
        n = Note(60)
        with pytest.raises(PropellerValidationError) as exc_info:
            n(200)
        msg = str(exc_info.value).lower()
        assert 'velocity' in msg
        assert '0' in msg
        assert '127' in msg

    def test_call_velocity_negative_raises(self):
        n = Note(60)
        with pytest.raises(PropellerValidationError) as exc_info:
            n(-5)
        msg = str(exc_info.value).lower()
        assert 'velocity' in msg
        assert '0' in msg
        assert '127' in msg


class TestNoteComposability:
    def test_call_then_mul(self):
        n = Note(60)
        result = n(120) * 2
        assert result.pitch == 60
        assert result.velocity == 120
        assert result.duration == 2.0


class TestRest:
    def test_rest_default_duration(self):
        r = Rest()
        assert r.duration == 1.0

    def test_rest_mul_returns_new_rest(self):
        r = Rest()
        result = r * 2
        assert result.duration == 2.0

    def test_rest_mul_preserves_original(self):
        r = Rest()
        _ = r * 2
        assert r.duration == 1.0

    def test_rest_immutable(self):
        r = Rest()
        with pytest.raises(Exception):
            r.duration = 3.0

    def test_rest_mul_zero_raises_validation_error(self):
        r = Rest()
        with pytest.raises(PropellerValidationError) as exc_info:
            r * 0
        assert 'duration' in str(exc_info.value)

    def test_rest_mul_negative_raises_validation_error(self):
        r = Rest()
        with pytest.raises(PropellerValidationError) as exc_info:
            r * -2
        assert 'duration' in str(exc_info.value)

    def test_rest_mul_two_beats_succeeds(self):
        r = Rest()
        result = r * 2
        assert result.duration == 2.0
