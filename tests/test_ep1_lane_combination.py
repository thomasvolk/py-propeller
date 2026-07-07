"""Tests for EP-1: Pitch Bend Lane Combination."""
import pytest
from propeller.errors import PropellerValidationError


# ---------------------------------------------------------------------------
# T-01 / T-02 — _serialize_lane: emit_trailing_pb parameter
# ---------------------------------------------------------------------------

class TestSerializeLaneTrailingPB:
    def _serialize_lane(self, lane, **kw):
        from propeller.serializer import _serialize_lane
        return _serialize_lane(lane, **kw)

    def test_t01_trailing_pb_emitted_when_flag_true(self):
        from propeller.notes import PB, Z
        notes_out, pbs_out = self._serialize_lane([Z, PB(0.5)], emit_trailing_pb=True)
        assert notes_out == []
        assert pbs_out == [[480, 12287]]

    def test_t01_trailing_pb_discarded_when_flag_false(self):
        from propeller.notes import PB, Z
        notes_out, pbs_out = self._serialize_lane([Z, PB(0.5)], emit_trailing_pb=False)
        assert pbs_out == []

    def test_t01_trailing_pb_discarded_by_default(self):
        from propeller.notes import PB, Z
        notes_out, pbs_out = self._serialize_lane([Z, PB(0.5)])
        assert pbs_out == []


# ---------------------------------------------------------------------------
# T-03 / T-04 — _serialize_track: multi-lane path uses emit_trailing_pb=True
# ---------------------------------------------------------------------------

class TestSerializeTrackMultiLane:
    def _serialize_track(self, notes):
        from propeller.composition import Track
        from propeller.serializer import _serialize_track
        track = Track(name='Test', channel=1, instrument=0, notes=notes)
        return _serialize_track(track)

    def test_t03_pb_only_lane_included_in_output(self):
        from propeller.notes import PB, Z, D4
        result = self._serialize_track([
            [D4],
            [Z, PB(0.5)],
        ])
        assert [480, 12287] in result['pitch-bends']

    def test_t03_pb_only_lane_contributes_no_notes(self):
        from propeller.notes import PB, Z, D4
        result = self._serialize_track([
            [D4],
            [Z, PB(0.5)],
        ])
        assert len(result['notes']) == 1

    def test_t03_note_lane_unaffected(self):
        from propeller.notes import PB, Z, D4
        result = self._serialize_track([
            [D4],
            [Z, PB(0.5)],
        ])
        assert result['notes'][0][2] == D4.pitch


# ---------------------------------------------------------------------------
# T-05 / T-06 — _serialize_lane: intermediate PB flush
# ---------------------------------------------------------------------------

class TestSerializeLaneIntermediatePB:
    def _serialize_lane(self, lane, **kw):
        from propeller.serializer import _serialize_lane
        return _serialize_lane(lane, **kw)

    def test_t05_multi_pb_lane_emits_all(self):
        from propeller.notes import PB, Z
        notes_out, pbs_out = self._serialize_lane(
            [PB(0.1), Z, PB(0.5), Z], emit_trailing_pb=True
        )
        assert notes_out == []
        assert pbs_out == [[0, 9011], [480, 12287]]

    def test_t05_intermediate_pb_not_lost(self):
        from propeller.notes import PB, Z, C4
        # PB(0.1) before rest, PB(0.5) before note — both must appear
        notes_out, pbs_out = self._serialize_lane([PB(0.1), Z, PB(0.5), C4])
        assert [0, 9011] in pbs_out
        assert [480, 12287] in pbs_out


# ---------------------------------------------------------------------------
# T-07 / T-08 — _serialize_track: same-tick collision raises error
# ---------------------------------------------------------------------------

class TestSerializeTrackCollision:
    def _serialize_track(self, notes):
        from propeller.composition import Track
        from propeller.serializer import _serialize_track
        track = Track(name='Test', channel=1, instrument=0, notes=notes)
        return _serialize_track(track)

    def test_t07_same_tick_raises(self):
        from propeller.notes import PB, D4, C4
        with pytest.raises(PropellerValidationError):
            self._serialize_track([
                [PB(0.0), D4 * 4],
                [PB(0.5), C4 * 4],
            ])

    def test_t07_different_ticks_does_not_raise(self):
        from propeller.notes import PB, Z, D4
        result = self._serialize_track([
            [PB(0.0), D4 * 4],
            [Z, PB(0.5)],
        ])
        assert len(result['pitch-bends']) == 2

    def test_t07_raises_propeller_validation_error_not_value_error(self):
        from propeller.notes import PB, D4, C4
        try:
            self._serialize_track([
                [PB(0.0), D4 * 4],
                [PB(0.5), C4 * 4],
            ])
        except ValueError:
            pytest.fail('Should not raise plain ValueError')
        except PropellerValidationError:
            pass


# ---------------------------------------------------------------------------
# T-09 — Integration test: AC-1 exact scenario
# ---------------------------------------------------------------------------

class TestIntegrationAC1:
    def test_t09_ac1_full_project(self):
        from propeller.notes import D4, F4, A4, PB, Z
        from propeller.serializer import serialize
        from tests.stubs import StubProject
        from propeller.composition import Track

        track = Track(
            name='Lead',
            channel=1,
            instrument=0,
            notes=[
                [PB(0.0), D4 * 4],
                [Z, F4 * 2],
                [Z * 2, A4 * 4],
                [Z, PB(0.5)],
            ],
        )
        p = StubProject(bpm=80, time_signature=(4, 4), bars=2, tracks=[track])
        result = serialize(p)
        track_out = result['tracks'][0]
        assert track_out['pitch-bends'] == [[0, 8192], [480, 12287]]


# ---------------------------------------------------------------------------
# T-10 — PB-only lane contributes zero note entries (AC-3)
# ---------------------------------------------------------------------------

class TestPBOnlyLaneNoNotes:
    def test_t10_pb_only_lane_no_note_entries(self):
        from propeller.notes import PB, Z, D4
        from propeller.composition import Track
        from propeller.serializer import _serialize_track

        track = Track(
            name='Test',
            channel=1,
            instrument=0,
            notes=[
                [D4 * 2],
                [Z, PB(0.5)],
            ],
        )
        result = _serialize_track(track)
        assert len(result['notes']) == 1
        assert result['notes'][0][2] == D4.pitch


# ---------------------------------------------------------------------------
# T-11 — Pitch bends sorted by ascending tick (AC-2)
# ---------------------------------------------------------------------------

class TestPitchBendSortOrder:
    def test_t11_pbs_sorted_ascending(self):
        from propeller.notes import PB, Z, D4, C4
        from propeller.composition import Track
        from propeller.serializer import _serialize_track

        # Lane 1 has PB at tick 480; lane 0 has PB at tick 0 — merged result must be sorted
        track = Track(
            name='Test',
            channel=1,
            instrument=0,
            notes=[
                [Z, PB(0.5)],   # PB at tick 480
                [PB(0.0), D4],  # PB at tick 0
            ],
        )
        result = _serialize_track(track)
        ticks = [pb[0] for pb in result['pitch-bends']]
        assert ticks == sorted(ticks)
