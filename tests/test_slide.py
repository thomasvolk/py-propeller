"""Tests for EP-1: Single-note pitch-bend glide (propeller.notes.Slide)."""
import pytest

from propeller.errors import PropellerValidationError


# ---------------------------------------------------------------------------
# T-1 to T-2: SlideTarget / to() construction
# ---------------------------------------------------------------------------

class TestSlideTargetConstruction:
    def test_t1_to_returns_slide_target_with_value(self):
        from propeller.notes.Slide import to, SlideTarget
        target = to(1.0)
        assert isinstance(target, SlideTarget)
        assert target.value == 1.0

    def test_t1_steps_defaults_to_point_zero_one(self):
        from propeller.notes.Slide import to
        target = to(1.0)
        assert target.steps == 0.01

    def test_t1_explicit_steps(self):
        from propeller.notes.Slide import to
        target = to(1.0, steps=0.05)
        assert target.steps == 0.05

    def test_t1_negative_value(self):
        from propeller.notes.Slide import to
        target = to(-0.5)
        assert target.value == -0.5

    def test_t1_immutable(self):
        from propeller.notes.Slide import to
        target = to(1.0)
        with pytest.raises(Exception):
            target.value = 0.5


# ---------------------------------------------------------------------------
# T-3 to T-4: SlideTarget validation
# ---------------------------------------------------------------------------

class TestSlideTargetValidation:
    def test_t3_value_above_one_raises(self):
        from propeller.notes.Slide import to
        with pytest.raises(PropellerValidationError):
            to(1.5)

    def test_t3_value_below_negative_one_raises(self):
        from propeller.notes.Slide import to
        with pytest.raises(PropellerValidationError):
            to(-1.5)

    def test_t3_value_exactly_one_is_valid(self):
        from propeller.notes.Slide import to
        assert to(1.0).value == 1.0

    def test_t3_value_exactly_negative_one_is_valid(self):
        from propeller.notes.Slide import to
        assert to(-1.0).value == -1.0

    def test_t3_value_zero_raises(self):
        from propeller.notes.Slide import to
        with pytest.raises(PropellerValidationError) as exc_info:
            to(0.0)
        assert '0.0' in str(exc_info.value)

    def test_t3_steps_zero_raises(self):
        from propeller.notes.Slide import to
        with pytest.raises(PropellerValidationError) as exc_info:
            to(1.0, steps=0)
        assert 'steps' in str(exc_info.value)

    def test_t3_steps_negative_raises(self):
        from propeller.notes.Slide import to
        with pytest.raises(PropellerValidationError):
            to(1.0, steps=-0.1)

    def test_t3_steps_above_one_raises(self):
        from propeller.notes.Slide import to
        with pytest.raises(PropellerValidationError):
            to(1.0, steps=1.1)

    def test_t3_steps_exactly_one_is_valid(self):
        from propeller.notes.Slide import to
        assert to(1.0, steps=1.0).steps == 1.0

    def test_t3_raises_propeller_validation_error_not_value_error(self):
        from propeller.notes.Slide import to
        try:
            to(0.0)
        except ValueError:
            pytest.fail("Should not raise plain ValueError")
        except PropellerValidationError:
            pass


# ---------------------------------------------------------------------------
# T-5 to T-6: Slide construction and the required import shapes
# ---------------------------------------------------------------------------

class TestSlideConstruction:
    def test_t5_fields_are_readable(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        target = to(1.0, steps=0.01)
        s = Slide(C4, target)
        assert s.start == C4
        assert s.target == target

    def test_t5_default_duration_is_one(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0))
        assert s.duration == 1.0

    def test_t5_explicit_duration(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0), duration=2.0)
        assert s.duration == 2.0

    def test_t5_immutable(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0))
        with pytest.raises(Exception):
            s.duration = 2.0

    def test_t5_import_slide_from_notes_package(self):
        from propeller.notes import Slide
        assert Slide.__name__ == 'Slide'

    def test_t5_import_to_from_slide_submodule(self):
        from propeller.notes.Slide import to
        assert callable(to)

    def test_t5_both_import_shapes_agree_on_slide_type(self):
        from propeller.notes import Slide as PackageSlide
        from propeller.notes.Slide import Slide as SubmoduleSlide
        assert PackageSlide is SubmoduleSlide


# ---------------------------------------------------------------------------
# T-7 to T-8: Slide construction validation
# ---------------------------------------------------------------------------

class TestSlideValidation:
    def test_t7_non_note_start_raises(self):
        from propeller.notes import Slide
        from propeller.notes.Slide import to
        with pytest.raises(PropellerValidationError) as exc_info:
            Slide(60, to(1.0))
        assert 'start' in str(exc_info.value) or 'Note' in str(exc_info.value)

    def test_t7_non_slide_target_raises(self):
        from propeller.notes import Slide, C4
        with pytest.raises(PropellerValidationError) as exc_info:
            Slide(C4, 1.0)
        assert 'target' in str(exc_info.value)

    def test_t7_old_two_note_call_shape_rejected(self):
        # AC-9: Slide(C4, D4), the retired two-Note call shape, is not a
        # supported invocation now that the second argument must be a
        # SlideTarget produced by to(...).
        from propeller.notes import Slide, C4, D4
        with pytest.raises(PropellerValidationError):
            Slide(C4, D4)

    def test_t7_raises_propeller_validation_error_not_value_error(self):
        from propeller.notes import Slide, C4
        try:
            Slide(C4, 1.0)
        except ValueError:
            pytest.fail("Should not raise plain ValueError")
        except PropellerValidationError:
            pass


# ---------------------------------------------------------------------------
# T-9 to T-10: Slide * n
# ---------------------------------------------------------------------------

class TestSlideMul:
    def test_t9_mul_returns_new_slide_with_updated_duration(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0))
        result = s * 4
        assert result.duration == 4.0

    def test_t9_mul_preserves_original(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0))
        _ = s * 4
        assert s.duration == 1.0

    def test_t9_mul_preserves_start_and_target(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        target = to(1.0, steps=0.05)
        s = Slide(C4, target)
        result = s * 4
        assert result.start == C4
        assert result.target == target

    def test_t9_mul_float_duration(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0))
        result = s * 0.5
        assert result.duration == 0.5

    def test_t9_mul_zero_raises_validation_error(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0))
        with pytest.raises(PropellerValidationError) as exc_info:
            s * 0
        assert 'duration' in str(exc_info.value)

    def test_t9_mul_negative_raises_validation_error(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0))
        with pytest.raises(PropellerValidationError):
            s * -1


# ---------------------------------------------------------------------------
# T-11 to T-12: _slide_pitch_bend_values ramp generation
# ---------------------------------------------------------------------------

class TestSlidePitchBendValues:
    def _values(self, value, steps):
        from propeller.serializer import _slide_pitch_bend_values
        return _slide_pitch_bend_values(value, steps)

    def test_t11_full_positive_range_produces_hundred_values(self):
        values = self._values(1.0, 0.01)
        assert len(values) == 100

    def test_t11_values_evenly_spaced_in_step_increments(self):
        values = self._values(1.0, 0.01)
        expected = [round(0.01 * i, 10) for i in range(1, 101)]
        assert [round(v, 10) for v in values] == expected

    def test_t11_last_value_equals_target(self):
        values = self._values(1.0, 0.01)
        assert values[-1] == pytest.approx(1.0)

    def test_t11_increments_no_larger_than_steps_when_evenly_divisible(self):
        values = self._values(1.0, 0.01)
        diffs = [values[0]] + [values[i] - values[i - 1] for i in range(1, len(values))]
        assert all(d <= 0.01 + 1e-9 for d in diffs)

    def test_t11_half_negative_range(self):
        # briefing example: to(-0.5) at the default steps=0.01 -> 50 values
        values = self._values(-0.5, 0.01)
        assert len(values) == 50
        assert values[-1] == pytest.approx(-0.5)
        assert all(v <= 0 for v in values)

    def test_t11_ac7_non_evenly_dividing_steps_rounds_to_nearest(self):
        # steps=0.03 does not evenly divide 1.0; round(1.0/0.03) == 33
        values = self._values(1.0, 0.03)
        assert len(values) == 33

    def test_t11_ac7_last_value_still_equals_target(self):
        values = self._values(1.0, 0.03)
        assert values[-1] == pytest.approx(1.0)

    def test_t11_no_validation_error_on_non_dividing_steps(self):
        self._values(1.0, 0.3)  # must not raise

    def test_t11_small_value_still_produces_at_least_one_event(self):
        values = self._values(0.001, 0.01)
        assert len(values) == 1
        assert values[0] == pytest.approx(0.001)


# ---------------------------------------------------------------------------
# T-13 to T-14: _expand_slide
# ---------------------------------------------------------------------------

class TestExpandSlide:
    def _expand(self, slide, start_tick=0, denominator=4):
        from propeller.serializer import _expand_slide
        return _expand_slide(slide, start_tick, denominator)

    def test_t13_exactly_one_note_row(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0, steps=0.01)) * 4
        notes_out, _pbs, _ticks = self._expand(s)
        assert len(notes_out) == 1

    def test_t13_note_row_spans_full_duration(self):
        # 4 beats @ denom 4 -> 1920 ticks
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0, steps=0.01)) * 4
        notes_out, _pbs, total_ticks = self._expand(s)
        assert notes_out[0] == [0, 1920, 60, 100]
        assert total_ticks == 1920

    def test_t13_note_uses_start_pitch_and_velocity(self):
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4(80), to(1.0, steps=0.01)) * 4
        notes_out, _pbs, _ticks = self._expand(s)
        assert notes_out[0][2] == 60
        assert notes_out[0][3] == 80

    def test_t13_leading_pitch_bend_is_zero_reset(self):
        from propeller.serializer import _pb_to_int
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0, steps=0.01)) * 4
        _notes, pbs, _ticks = self._expand(s, start_tick=100)
        assert pbs[0] == [100, _pb_to_int(0.0)]

    def test_t13_trailing_pitch_bend_is_zero_reset_at_end_tick(self):
        from propeller.serializer import _pb_to_int
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0, steps=0.01)) * 4
        _notes, pbs, total_ticks = self._expand(s, start_tick=100)
        assert pbs[-1] == [100 + total_ticks, _pb_to_int(0.0)]

    def test_t13_ramp_event_count_matches_slide_pitch_bend_values(self):
        # 1 leading zero-reset + 100 ramp events (last one overwritten by the
        # trailing zero-reset in place, not appended) = 101 total rows.
        from propeller.notes import Slide, C4
        from propeller.notes.Slide import to
        s = Slide(C4, to(1.0, steps=0.01)) * 4
        _notes, pbs, _ticks = self._expand(s)
        assert len(pbs) == 101

    def test_t13_ramp_values_match_target_direction(self):
        from propeller.serializer import _pb_to_int
        from propeller.notes import Slide, D4
        from propeller.notes.Slide import to
        s = Slide(D4, to(-0.5)) * 4
        _notes, pbs, _ticks = self._expand(s)
        # index 0 is the leading zero-reset; index 1 is the first ramp step
        assert pbs[1][1] == _pb_to_int(-0.01)


# ---------------------------------------------------------------------------
# T-15 to T-16: same-tick pitch-bend collision dedup within one lane
# ---------------------------------------------------------------------------

class TestSameTickDedup:
    def test_t15_slide_immediately_followed_by_pb_keeps_first(self):
        # The Slide's end-of-glide zero-reset lands on the same tick as the
        # immediately-following manual PB flush (no rest between them); only
        # the Slide's earlier-written reset survives.
        from propeller.serializer import _serialize_lane, _pb_to_int
        from propeller.notes import Slide, C4, PB
        from propeller.notes.Slide import to
        lane = [Slide(C4, to(1.0, steps=0.5)), PB(0.9)]
        _notes_out, pbs_out = _serialize_lane(lane)
        ticks = [pb[0] for pb in pbs_out]
        assert len(ticks) == len(set(ticks))
        last_tick = ticks[-1]
        assert [pb for pb in pbs_out if pb[0] == last_tick] == [[last_tick, _pb_to_int(0.0)]]

    def test_t15_slide_immediately_followed_by_slide_keeps_first(self):
        from propeller.serializer import _serialize_lane
        from propeller.notes import Slide, C4, D4
        from propeller.notes.Slide import to
        lane = [Slide(C4, to(1.0, steps=0.5)), Slide(D4, to(-1.0, steps=0.5))]
        _notes_out, pbs_out = _serialize_lane(lane)
        ticks = [pb[0] for pb in pbs_out]
        assert len(ticks) == len(set(ticks))

    def test_t15_dedup_applies_to_tagged_output_too(self):
        from propeller.serializer import _serialize_lane
        from propeller.notes import Slide, C4, PB
        from propeller.notes.Slide import to
        lane = [Slide(C4, to(1.0, steps=0.5)), PB(0.9)]
        _notes_out, pbs_out = _serialize_lane(lane, tag_source=True)
        ticks = [row[0] for row in pbs_out]
        assert len(ticks) == len(set(ticks))

    def test_t15_non_colliding_events_all_preserved(self):
        from propeller.serializer import _serialize_lane
        from propeller.notes import Slide, C4, Z, PB
        from propeller.notes.Slide import to
        lane = [Slide(C4, to(1.0, steps=0.5)), Z, PB(0.9)]
        _notes_out, pbs_out = _serialize_lane(lane, emit_trailing_pb=True)
        ticks = [pb[0] for pb in pbs_out]
        assert len(ticks) == len(set(ticks))
        assert len(pbs_out) == 4  # 3 slide pitch-bends + 1 manual, none colliding


# ---------------------------------------------------------------------------
# T-17: full serialization worked examples (briefing.md)
# ---------------------------------------------------------------------------

class TestSlideSerialization:
    def _serialize(self, note, target, beats=4, bars=4):
        from propeller.composition import Project, Track
        from propeller.notes import Slide
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0,
                      notes=[Slide(note, target) * beats])
        project = Project(bpm=120, time_signature=(4, 4), bars=bars, tracks=[track])
        return serialize(project)

    def test_t17_ascending_example_single_note_event(self):
        # Slide(C4, to(1.0, steps=0.01)) * 4
        from propeller.notes.Slide import to
        from propeller.notes import C4
        result = self._serialize(C4, to(1.0, steps=0.01))
        notes_out = result['tracks'][0]['notes']
        assert notes_out == [[0, 1920, 60, 100]]

    def test_t17_ascending_example_pitch_bend_count(self):
        from propeller.notes.Slide import to
        from propeller.notes import C4
        result = self._serialize(C4, to(1.0, steps=0.01))
        pbs = result['tracks'][0]['pitch-bends']
        assert len(pbs) == 101

    def test_t17_ascending_example_leading_and_trailing_zero_reset(self):
        from propeller.serializer import _pb_to_int
        from propeller.notes.Slide import to
        from propeller.notes import C4
        result = self._serialize(C4, to(1.0, steps=0.01))
        pbs = result['tracks'][0]['pitch-bends']
        assert pbs[0] == [0, _pb_to_int(0.0)]
        assert pbs[-1] == [1920, _pb_to_int(0.0)]

    def test_t17_ascending_example_ramp_monotonic(self):
        from propeller.notes.Slide import to
        from propeller.notes import C4
        result = self._serialize(C4, to(1.0, steps=0.01))
        pbs = result['tracks'][0]['pitch-bends']
        values = [pb[1] for pb in pbs[:-1]]  # exclude the trailing zero-reset
        assert values == sorted(values)

    def test_t17_descending_example_single_note_event(self):
        # Slide(D4, to(-0.5)) * 4, default steps
        from propeller.notes.Slide import to
        from propeller.notes import D4
        result = self._serialize(D4, to(-0.5))
        notes_out = result['tracks'][0]['notes']
        assert notes_out == [[0, 1920, 62, 100]]

    def test_t17_descending_example_pitch_bend_count(self):
        from propeller.notes.Slide import to
        from propeller.notes import D4
        result = self._serialize(D4, to(-0.5))
        pbs = result['tracks'][0]['pitch-bends']
        assert len(pbs) == 51

    def test_t17_descending_example_ramp_monotonic_decreasing(self):
        from propeller.notes.Slide import to
        from propeller.notes import D4
        result = self._serialize(D4, to(-0.5))
        pbs = result['tracks'][0]['pitch-bends']
        values = [pb[1] for pb in pbs[:-1]]
        assert values == sorted(values, reverse=True)

    def test_t17_duration_via_multiplication(self):
        from propeller.notes.Slide import to
        from propeller.notes import C4
        result = self._serialize(C4, to(1.0, steps=0.01), beats=2)
        notes_out = result['tracks'][0]['notes']
        assert notes_out[0][1] == 960

    def test_t17_slide_position_among_other_notes(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, D4
        from propeller.notes.Slide import to
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0,
                      notes=[D4, Slide(C4, to(1.0, steps=0.01)) * 4, D4])
        project = Project(bpm=120, time_signature=(4, 4), bars=8, tracks=[track])
        result = serialize(project)
        notes_out = result['tracks'][0]['notes']
        assert notes_out[0] == [0, 480, 62, 100]
        assert notes_out[1] == [480, 1920, 60, 100]
        assert notes_out[-1] == [2400, 480, 62, 100]

    def test_t17_old_shape_rejected_end_to_end(self):
        from propeller.notes import Slide, C4, D4
        with pytest.raises(PropellerValidationError):
            Slide(C4, D4)

    def test_t17_nf1_deterministic_across_repeated_calls(self):
        from propeller.notes.Slide import to
        from propeller.notes import C4
        result1 = self._serialize(C4, to(1.0, steps=0.01))
        result2 = self._serialize(C4, to(1.0, steps=0.01))
        assert result1 == result2

    def test_t17_serializer_does_not_touch_existing_note_pitch_bend_rest_handling(self):
        # Regression guard: a plain Note/Rest/PitchBend-only track still
        # serializes exactly as before this refactor.
        from propeller.composition import Project, Track
        from propeller.notes import C4, D4, PB
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0, notes=[PB(0.5), C4, D4])
        project = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track])
        result = serialize(project)
        notes_out = result['tracks'][0]['notes']
        pbs = result['tracks'][0]['pitch-bends']
        assert notes_out == [[0, 480, 60, 100], [480, 480, 62, 100]]
        assert pbs == [[0, 12287]]
