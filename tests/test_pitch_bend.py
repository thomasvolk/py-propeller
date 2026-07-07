"""Tests for EP-1: Pitch Bend DSL Element."""
import pytest
from propeller.errors import PropellerValidationError


# ---------------------------------------------------------------------------
# T-1 to T-5: PitchBend construction and validation
# ---------------------------------------------------------------------------

class TestPitchBendConstruction:
    def test_t1_value_0_5(self):
        from propeller.notes import PitchBend
        pb = PitchBend(0.5)
        assert pb.value == 0.5

    def test_t2_boundary_positive_one(self):
        from propeller.notes import PitchBend
        pb = PitchBend(1.0)
        assert pb.value == 1.0

    def test_t2_boundary_negative_one(self):
        from propeller.notes import PitchBend
        pb = PitchBend(-1.0)
        assert pb.value == -1.0

    def test_t2_default_value_is_zero(self):
        from propeller.notes import PitchBend
        pb = PitchBend()
        assert pb.value == 0.0

    def test_t3_out_of_range_positive_raises(self):
        from propeller.notes import PitchBend
        with pytest.raises(PropellerValidationError) as exc_info:
            PitchBend(1.5)
        msg = str(exc_info.value)
        assert '1.5' in msg
        assert '-1.0' in msg
        assert '1.0' in msg

    def test_t4_out_of_range_negative_raises(self):
        from propeller.notes import PitchBend
        with pytest.raises(PropellerValidationError):
            PitchBend(-1.5)

    def test_t5_raises_propeller_validation_error_not_value_error(self):
        from propeller.notes import PitchBend
        with pytest.raises(PropellerValidationError):
            PitchBend(2.0)

    def test_t5_not_plain_value_error(self):
        from propeller.notes import PitchBend
        try:
            PitchBend(2.0)
        except ValueError:
            pytest.fail("Should not raise plain ValueError")
        except PropellerValidationError:
            pass

    def test_t5_not_plain_type_error(self):
        from propeller.notes import PitchBend
        try:
            PitchBend(2.0)
        except TypeError:
            pytest.fail("Should not raise plain TypeError")
        except PropellerValidationError:
            pass

    def test_frozen_immutable(self):
        from propeller.notes import PitchBend
        pb = PitchBend(0.5)
        with pytest.raises(Exception):
            pb.value = 0.9


# ---------------------------------------------------------------------------
# T-6 to T-8: PB constant and __call__
# ---------------------------------------------------------------------------

class TestPBConstant:
    def test_t6_pb_is_pitch_bend_instance(self):
        from propeller.notes import PB, PitchBend
        assert isinstance(PB, PitchBend)

    def test_t6_pb_value_is_zero(self):
        from propeller.notes import PB
        assert PB.value == 0.0

    def test_t7_pb_call_returns_pitch_bend_with_value(self):
        from propeller.notes import PB, PitchBend
        result = PB(0.5)
        assert isinstance(result, PitchBend)
        assert result.value == 0.5

    def test_t7_pb_call_returns_new_instance(self):
        from propeller.notes import PB
        result = PB(0.5)
        assert result is not PB

    def test_t8_pb_in_all(self):
        import propeller.notes as notes_mod
        assert 'PB' in notes_mod.__all__

    def test_t8_pitch_bend_not_in_all(self):
        import propeller.notes as notes_mod
        assert 'PitchBend' not in notes_mod.__all__


# ---------------------------------------------------------------------------
# T-9 to T-16: Track validation with PitchBend
# ---------------------------------------------------------------------------

class TestTrackWithPitchBend:
    def _make_track(self, notes):
        from propeller.composition import Track
        return Track(name='Test', channel=1, instrument=0, notes=notes)

    def test_t9_track_accepts_pb_before_note(self):
        from propeller.notes import PB, C4
        self._make_track([PB(0.5), C4])  # must not raise

    def test_t10_track_accepts_trailing_pb(self):
        from propeller.notes import PB, C4
        self._make_track([C4, PB(0.3)])  # must not raise

    def test_t11_consecutive_pbs_before_note_raises(self):
        from propeller.notes import PB, D4
        with pytest.raises(PropellerValidationError):
            self._make_track([PB(0.5), PB(-0.3), D4])

    def test_t12_consecutive_pbs_raises_propeller_validation_error(self):
        from propeller.notes import PB, D4
        with pytest.raises(PropellerValidationError):
            self._make_track([PB(0.5), PB(-0.3), D4])

    def test_t12_not_plain_value_error(self):
        from propeller.notes import PB, D4
        try:
            self._make_track([PB(0.5), PB(-0.3), D4])
        except ValueError:
            pytest.fail("Should not raise plain ValueError")
        except PropellerValidationError:
            pass

    def test_t13_track_without_pb_behaves_identically(self):
        from propeller.notes import C4, D4
        from propeller.serializer import serialize
        from tests.stubs import StubProject
        track = self._make_track([C4, D4])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[track])
        result = serialize(p)
        notes_out = result['tracks'][0]['notes']
        assert len(notes_out) == 2
        assert notes_out[0] == [0, 480, C4.pitch, C4.velocity]
        assert notes_out[1] == [480, 480, D4.pitch, D4.velocity]

    def test_t14_trailing_consecutive_pbs_raises(self):
        from propeller.notes import PB, C4
        with pytest.raises(PropellerValidationError):
            self._make_track([C4, PB(0.5), PB(-0.3)])

    def test_t15_multilane_non_consecutive_per_lane_accepted(self):
        from propeller.notes import PB, C4, D4
        from propeller.composition import Track
        lane1 = [PB(0.5), C4]
        lane2 = [PB(-0.3), D4]
        Track(name='Test', channel=1, instrument=0, notes=[lane1, lane2])  # no error

    def test_t16_multilane_consecutive_pbs_in_one_lane_raises(self):
        from propeller.notes import PB, C4
        from propeller.composition import Track
        lane1 = [PB(0.5), PB(-0.3), C4]
        lane2 = [C4]
        with pytest.raises(PropellerValidationError):
            Track(name='Test', channel=1, instrument=0, notes=[lane1, lane2])


# ---------------------------------------------------------------------------
# T-17 to T-20: Serializer with PitchBend
# ---------------------------------------------------------------------------

class TestSerializerWithPitchBend:
    def _serialize_lane(self, lane):
        from propeller.serializer import _serialize_lane
        return _serialize_lane(lane)

    def _serialize_track_dict(self, notes):
        from propeller.composition import Track
        from propeller.serializer import _serialize_track
        track = Track(name='Test', channel=1, instrument=0, notes=notes)
        return _serialize_track(track)

    def test_t17_pb_does_not_advance_tick_cursor(self):
        from propeller.notes import PB, C4
        notes_out, pitch_bends_out = self._serialize_lane([PB(0.5), C4])
        assert len(notes_out) == 1
        assert notes_out[0][0] == 0  # note starts at tick 0, not advanced

    def test_t17_pitch_bend_emitted_at_same_tick_as_note(self):
        from propeller.notes import PB, C4
        notes_out, pitch_bends_out = self._serialize_lane([PB(0.5), C4])
        assert len(pitch_bends_out) == 1
        assert pitch_bends_out[0][0] == 0  # same tick as the note

    def test_t18_serialized_track_has_pitch_bends_key(self):
        from propeller.notes import PB, C4
        track_dict = self._serialize_track_dict([PB(0.5), C4])
        assert 'pitch-bends' in track_dict

    def test_t18_pitch_bends_entry_is_tick_int_value_pair(self):
        from propeller.notes import PB, C4
        track_dict = self._serialize_track_dict([PB(0.5), C4])
        # value is a 14-bit integer: int(round((0.5 + 1.0) / 2.0 * 16383)) == 12287
        assert track_dict['pitch-bends'] == [[0, 12287]]

    def test_t19_trailing_pb_is_discarded(self):
        from propeller.notes import PB, C4
        # Trailing PB with no following note is silently discarded (EP-2 F-8)
        notes_out, pitch_bends_out = self._serialize_lane([C4, PB(0.3)])
        assert len(pitch_bends_out) == 0

    def test_t20_no_pb_track_has_no_pitch_bends_key(self):
        from propeller.notes import C4, D4
        track_dict = self._serialize_track_dict([C4, D4])
        assert 'pitch-bends' not in track_dict
