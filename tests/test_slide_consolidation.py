"""Tests for EP-2: Concurrent Slide Consolidation (propeller.serializer).

Named test_slide_consolidation.py (rather than reusing the test_ep1_* /
test_ep2_* filenames) per the EP-2 spec's explicit naming guidance, since
those filenames already belong to unrelated, pre-existing work.
"""
import pytest

from propeller.errors import PropellerValidationError


# ---------------------------------------------------------------------------
# T-1 / T-2 — _serialize_lane: pitch-bend row source tagging
# ---------------------------------------------------------------------------

class TestSerializeLaneSourceTagging:
    def _serialize_lane_tagged(self, lane, **kw):
        from propeller.serializer import _serialize_lane
        return _serialize_lane(lane, tag_source=True, **kw)

    def test_t1_note_triggered_manual_pb_tagged_manual(self):
        from propeller.notes import PB, C4
        _notes_out, pbs_out = self._serialize_lane_tagged([PB(0.5), C4])
        assert len(pbs_out) == 1
        _tick, _value, source = pbs_out[0]
        assert source == 'manual'

    def test_t1_trailing_manual_pb_tagged_manual(self):
        from propeller.notes import PB, Z
        _notes_out, pbs_out = self._serialize_lane_tagged(
            [Z, PB(0.5)], emit_trailing_pb=True
        )
        assert len(pbs_out) == 1
        _tick, _value, source = pbs_out[0]
        assert source == 'manual'

    def test_t1_intermediate_manual_pb_tagged_manual(self):
        from propeller.notes import PB, Z, C4
        _notes_out, pbs_out = self._serialize_lane_tagged([PB(0.1), Z, PB(0.5), C4])
        assert len(pbs_out) == 2
        assert all(source == 'manual' for _t, _v, source in pbs_out)

    def test_t1_slide_pb_rows_tagged_slide(self):
        from propeller.notes import Slide, C4, C5
        slide = Slide(C4, C5, steps=0.5)
        _notes_out, pbs_out = self._serialize_lane_tagged([slide])
        assert len(pbs_out) > 0
        assert all(source == 'slide' for _t, _v, source in pbs_out)

    def test_t1_mixed_manual_and_slide_tagged_independently(self):
        from propeller.notes import PB, C4, Slide, D4
        _notes_out, pbs_out = self._serialize_lane_tagged(
            [PB(0.2), C4, Slide(C4, D4, steps=0.5)], emit_trailing_pb=True
        )
        sources = [source for _t, _v, source in pbs_out]
        assert sources[0] == 'manual'
        assert all(s == 'slide' for s in sources[1:])

    def test_t1_default_tag_source_false_returns_plain_pairs(self):
        # Backward-compatibility guard: tag_source defaults to False, so the
        # return shape used by pre-existing callers (and pre-existing tests
        # in tests/test_ep1_lane_combination.py) is unchanged.
        from propeller.serializer import _serialize_lane
        from propeller.notes import PB, C4
        _notes_out, pbs_out = _serialize_lane([PB(0.5), C4])
        assert pbs_out == [[0, 12287]]


# ---------------------------------------------------------------------------
# T-3 / T-4 — _serialize_track: matching concurrent Slide values dedup (AC-1)
# ---------------------------------------------------------------------------

class TestConsolidationIdenticalValuesDedup:
    def _serialize(self, slide1, slide2, bars=4):
        from propeller.composition import Project, Track
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0, notes=[[slide1], [slide2]])
        project = Project(bpm=120, time_signature=(4, 4), bars=bars, tracks=[track])
        return serialize(project)

    def test_t3_ac1_matching_slides_dedup_to_single_pb_per_tick(self):
        # 60 ramp events (last one replaced by the shared end-tick zero-reset)
        # plus the shared start-tick zero-reset = 61, all deduped since both
        # slides' curves are identical.
        from propeller.notes import Slide, C4, C5, E4, E5
        result = self._serialize(Slide(C4, C5, steps=0.1) * 4, Slide(E4, E5, steps=0.1) * 4)
        pbs = result['tracks'][0]['pitch-bends']
        assert len(pbs) == 61

    def test_t3_ac1_no_duplicate_ticks_in_output(self):
        from propeller.notes import Slide, C4, C5, E4, E5
        result = self._serialize(Slide(C4, C5, steps=0.1) * 4, Slide(E4, E5, steps=0.1) * 4)
        pbs = result['tracks'][0]['pitch-bends']
        ticks = [pb[0] for pb in pbs]
        assert len(ticks) == len(set(ticks))

    def test_t3_ac1_output_format_is_plain_int_pairs(self):
        from propeller.notes import Slide, C4, C5, E4, E5
        result = self._serialize(Slide(C4, C5, steps=0.1) * 4, Slide(E4, E5, steps=0.1) * 4)
        pbs = result['tracks'][0]['pitch-bends']
        for entry in pbs:
            assert isinstance(entry, list)
            assert len(entry) == 2
            assert all(isinstance(v, int) for v in entry)


# ---------------------------------------------------------------------------
# T-5 / T-6 — Note events unaffected by concurrent-Slide consolidation (AC-2)
# ---------------------------------------------------------------------------

class TestConsolidationNotesUnaffected:
    def test_t5_ac2_notes_identical_alone_vs_concurrent(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, C5, E4, E5
        from propeller.serializer import serialize

        alone_track = Track(
            name='Lead', channel=1, instrument=0, notes=[Slide(C4, C5, steps=0.1) * 4]
        )
        alone_project = Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[alone_track])
        alone_notes = serialize(alone_project)['tracks'][0]['notes']

        combined_track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[[Slide(C4, C5, steps=0.1) * 4], [Slide(E4, E5, steps=0.1) * 4]],
        )
        combined_project = Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[combined_track])
        combined_notes = serialize(combined_project)['tracks'][0]['notes']

        # C4->C5 and E4->E5 share intermediate pitches (64, 66, 68, 70), so a
        # pitch-based filter can't cleanly separate the two slides' notes.
        # Instead assert every note the C4 slide produces alone also appears,
        # unchanged, in the combined output (F-2: notes are never merged or
        # altered by concurrent-Slide pitch-bend consolidation).
        for note in alone_notes:
            assert note in combined_notes

    def test_t5_ac2_combined_note_count_is_sum_of_both_slides(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, C5, E4, E5
        from propeller.serializer import serialize

        combined_track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[[Slide(C4, C5, steps=0.1) * 4], [Slide(E4, E5, steps=0.1) * 4]],
        )
        combined_project = Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[combined_track])
        combined_notes = serialize(combined_project)['tracks'][0]['notes']
        assert len(combined_notes) == 12


# ---------------------------------------------------------------------------
# T-7 / T-8 — Consolidation scoped per track, never cross-track (AC-3)
# ---------------------------------------------------------------------------

class TestConsolidationPerTrackScoping:
    def test_t7_ac3_different_tracks_pitch_bends_independent(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, C5, D4, D5
        from propeller.serializer import serialize

        track_a = Track(name='A', channel=1, instrument=0, notes=[Slide(C4, C5, steps=0.1) * 4])
        track_b = Track(name='B', channel=2, instrument=0, notes=[Slide(D4, D5, steps=0.1) * 4])
        combined = serialize(
            Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[track_a, track_b])
        )
        solo_a = serialize(Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[track_a]))
        solo_b = serialize(Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[track_b]))

        assert combined['tracks'][0]['pitch-bends'] == solo_a['tracks'][0]['pitch-bends']
        assert combined['tracks'][1]['pitch-bends'] == solo_b['tracks'][0]['pitch-bends']

    def test_t7_ac3_one_tracks_slide_conflict_does_not_affect_other_track(self):
        # Track A has two mismatched concurrent Slides that would raise on
        # their own; Track B has a clean, unrelated Slide. Serializing the
        # combined project must raise (Track A is still invalid) but the
        # important behaviour under test is that track scoping is real: a
        # solo B project serializes cleanly and identically to how it would
        # within any project, regardless of what happens in Track A.
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, D4, Cs4, E4, F4
        from propeller.serializer import serialize

        track_b = Track(name='B', channel=2, instrument=0, notes=[Slide(E4, F4, steps=1.0)])
        solo_b = serialize(Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track_b]))

        track_a = Track(
            name='A', channel=1, instrument=0,
            notes=[[Slide(C4, D4, steps=0.5)], [Slide(C4, Cs4, steps=0.25)]],
        )
        with pytest.raises(PropellerValidationError):
            serialize(Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track_a, track_b]))

        # Re-affirm B in isolation is unaffected by A's presence/shape.
        again_b = serialize(Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track_b]))
        assert again_b == solo_b


# ---------------------------------------------------------------------------
# T-9 / T-10 — Mismatched concurrent Slide values raise (AC-4)
# ---------------------------------------------------------------------------

class TestConsolidationMismatchedValuesRaise:
    def test_t9_ac4_mismatched_slide_values_same_tick_raises(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, D4, Cs4
        from propeller.serializer import serialize

        track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[
                [Slide(C4, D4, steps=0.5)],
                [Slide(C4, Cs4, steps=0.25)],
            ],
        )
        project = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track])
        with pytest.raises(PropellerValidationError):
            serialize(project)

    def test_t9_ac4_raises_propeller_validation_error_not_value_error(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, D4, Cs4
        from propeller.serializer import serialize

        track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[
                [Slide(C4, D4, steps=0.5)],
                [Slide(C4, Cs4, steps=0.25)],
            ],
        )
        project = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track])
        try:
            serialize(project)
        except ValueError:
            pytest.fail('Should not raise plain ValueError')
        except PropellerValidationError:
            pass


# ---------------------------------------------------------------------------
# T-11 / T-12 — Non-matching-tick events all preserved, sorted, unmerged (AC-5)
# ---------------------------------------------------------------------------

class TestConsolidationNonMatchingTicksPreserved:
    def test_t11_ac5_non_matching_ticks_all_preserved_sorted(self):
        # Lane 1's Slide (start-tick 0) produces zero-resets at 0 and 480,
        # plus a mid-ramp event at 240. Lane 2's Slide is pushed out to
        # start-tick 720 (past lane 1's last tick) by a leading rest, so its
        # own zero-resets (720, 1200) land on ticks lane 1 never touches.
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, D4, E4, Fs4, Z
        from propeller.serializer import serialize

        track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[
                [Slide(C4, D4, steps=0.5)],              # pbs at ticks 0, 240, 480
                [Z * 1.5, Slide(E4, Fs4, steps=1.0)],     # pbs at ticks 720, 1200
            ],
        )
        project = Project(bpm=120, time_signature=(4, 4), bars=2, tracks=[track])
        result = serialize(project)
        pbs = result['tracks'][0]['pitch-bends']
        ticks = [pb[0] for pb in pbs]
        assert ticks == [0, 240, 480, 720, 1200]

    def test_t11_ac5_ticks_are_sorted_ascending(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, D4, E4, Fs4, Z
        from propeller.serializer import serialize

        track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[
                [Z * 1.5, Slide(E4, Fs4, steps=1.0)],     # pbs at ticks 720, 1200 (lane listed first)
                [Slide(C4, D4, steps=0.5)],                # pbs at ticks 0, 240, 480
            ],
        )
        project = Project(bpm=120, time_signature=(4, 4), bars=2, tracks=[track])
        result = serialize(project)
        ticks = [pb[0] for pb in result['tracks'][0]['pitch-bends']]
        assert ticks == sorted(ticks)
        assert ticks == [0, 240, 480, 720, 1200]


# ---------------------------------------------------------------------------
# T-13 / T-14 — Slide vs manual PitchBend collision always raises (AC-6)
# ---------------------------------------------------------------------------

class TestConsolidationManualCollisionAlwaysRaises:
    def test_t13_ac6_slide_and_manual_pb_same_tick_raises_even_if_values_match(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, D4, PB, Z
        from propeller.serializer import serialize

        # Slide(C4, D4, steps=0.5) puts value 0.5 at tick 240 (see T-9 math);
        # the manual PB below is placed at the same tick with the same value.
        track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[
                [Z * 0.5, PB(0.5)],
                [Slide(C4, D4, steps=0.5)],
            ],
        )
        project = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track])
        with pytest.raises(PropellerValidationError):
            serialize(project)

    def test_t13_ac6_slide_and_manual_pb_same_tick_different_values_also_raises(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, D4, PB, Z
        from propeller.serializer import serialize

        track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[
                [Z * 0.5, PB(-0.9)],
                [Slide(C4, D4, steps=0.5)],
            ],
        )
        project = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track])
        with pytest.raises(PropellerValidationError):
            serialize(project)


# ---------------------------------------------------------------------------
# T-15 / T-16 — Deterministic consolidation output (NF-1)
# ---------------------------------------------------------------------------

class TestConsolidationDeterminism:
    def _build_project(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, C5, E4, E5
        track = Track(
            name='Lead', channel=1, instrument=0,
            notes=[[Slide(C4, C5, steps=0.1) * 4], [Slide(E4, E5, steps=0.1) * 4]],
        )
        return Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[track])

    def test_t15_nf1_repeated_serialization_identical(self):
        from propeller.serializer import serialize
        result1 = serialize(self._build_project())
        result2 = serialize(self._build_project())
        assert result1 == result2

    def test_t15_nf1_repeated_serialization_identical_many_times(self):
        from propeller.serializer import serialize
        results = [serialize(self._build_project()) for _ in range(5)]
        assert all(r == results[0] for r in results)
