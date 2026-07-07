"""Tests for EP-2: Pitch Bend Serialization (14-bit values, pitch-bends key)."""
import pytest

from propeller.notes import PB, C4, D4, Z
from propeller.composition import Track
from propeller.serializer import serialize
from tests.stubs import StubProject, StubTrack


def _make_project(notes, bars=4):
    track = Track(name='Test', channel=1, instrument=0, notes=notes)
    return StubProject(bpm=120, time_signature=(4, 4), bars=bars, tracks=[track])


def _serialize_track_dict(notes, bars=4):
    return serialize(_make_project(notes, bars))['tracks'][0]


# ---------------------------------------------------------------------------
# T-1 to T-5: 14-bit conversion formula
# ---------------------------------------------------------------------------

class TestPbIntConversion:
    def test_t1_pb_neg1_yields_value_0(self):
        td = _serialize_track_dict([PB(-1.0), C4])
        assert td['pitch-bends'][0][1] == 0

    def test_t2_pb_zero_yields_value_8192(self):
        td = _serialize_track_dict([PB(0.0), C4])
        assert td['pitch-bends'][0][1] == 8192

    def test_t3_bare_pb_yields_value_8192(self):
        td = _serialize_track_dict([PB, C4])
        assert td['pitch-bends'][0][1] == 8192

    def test_t4_pb_pos1_yields_value_16383(self):
        td = _serialize_track_dict([PB(1.0), C4])
        assert td['pitch-bends'][0][1] == 16383

    def test_t5_pb_0_5_yields_value_greater_than_8192(self):
        td = _serialize_track_dict([PB(0.5), C4])
        assert td['pitch-bends'][0][1] > 8192


# ---------------------------------------------------------------------------
# T-6 to T-16: tick placement, ordering, omission
# ---------------------------------------------------------------------------

class TestPbTickAndOmission:
    def test_t6_pb_before_first_note_tick_is_0(self):
        td = _serialize_track_dict([PB(0.5), C4])
        assert td['pitch-bends'][0][0] == 0

    def test_t7_pb_between_notes_tick_equals_pb_position(self):
        # [C4(1 beat), PB(-0.5), D4] — PB appears at tick 480 (after C4)
        td = _serialize_track_dict([C4, PB(-0.5), D4])
        assert td['pitch-bends'][0][0] == 480

    def test_t8_no_pb_track_has_no_pitch_bends_key(self):
        td = _serialize_track_dict([C4, D4])
        assert 'pitch-bends' not in td

    def test_t9_trailing_pb_produces_no_pitch_bends_key(self):
        td = _serialize_track_dict([C4, PB(0.3)])
        assert 'pitch-bends' not in td
        assert 'pitch_bends' not in td

    def test_t10_two_pb_events_sorted_by_ascending_tick(self):
        # [PB(-0.3), C4, PB(0.5), D4] — PBs at ticks 0 and 480
        td = _serialize_track_dict([PB(-0.3), C4, PB(0.5), D4])
        pbs = td['pitch-bends']
        assert len(pbs) == 2
        assert pbs[0][0] < pbs[1][0]

    def test_t11_pb_tick_strictly_less_than_loop_duration(self):
        # loop_duration = 4 bars × 4 beats/bar × 480 = 7680
        td = _serialize_track_dict([PB(0.5), C4], bars=4)
        loop_duration = 4 * 4 * 480
        assert td['pitch-bends'][0][0] < loop_duration

    def test_t12_pb_free_project_output_identical(self):
        td = _serialize_track_dict([C4, D4])
        assert 'pitch-bends' not in td
        assert len(td['notes']) == 2

    def test_t15_pb_fires_at_pb_position_not_note_position(self):
        # [PB(0.5), Z(rest 1 beat), C4] — PB at tick 0, note at tick 480
        td = _serialize_track_dict([PB(0.5), Z, C4])
        assert td['pitch-bends'][0][0] == 0

    def test_t16_multilane_pitch_bends_merged_and_sorted(self):
        # lane1: [C4(1 beat), PB(0.5), D4] — PB at tick 480
        # lane2: [PB(-0.3), C4] — PB at tick 0
        # merged & sorted: tick 0, tick 480
        lane1 = [C4, PB(0.5), D4]
        lane2 = [PB(-0.3), C4]
        track = Track(name='Test', channel=1, instrument=0, notes=[lane1, lane2])
        project = StubProject(bpm=120, time_signature=(4, 4), bars=4, tracks=[track])
        td = serialize(project)['tracks'][0]
        pbs = td['pitch-bends']
        assert len(pbs) == 2
        assert pbs[0][0] == 0
        assert pbs[1][0] == 480


# ---------------------------------------------------------------------------
# T-13 to T-14: format validation and regression baseline
# ---------------------------------------------------------------------------

class TestPbFormatAndRegression:
    def test_t13_pitch_bends_format_is_list_of_int_pairs(self):
        td = _serialize_track_dict([PB(0.5), C4])
        pbs = td['pitch-bends']
        assert isinstance(pbs, list)
        for entry in pbs:
            assert isinstance(entry, list)
            assert len(entry) == 2
            assert all(isinstance(v, int) for v in entry)

    def test_t14_pb_free_project_notes_unchanged(self):
        td = _serialize_track_dict([C4, D4])
        assert 'pitch-bends' not in td
        assert td['notes'] == [
            [0, 480, C4.pitch, C4.velocity],
            [480, 480, D4.pitch, D4.velocity],
        ]
