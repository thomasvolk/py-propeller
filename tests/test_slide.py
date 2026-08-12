"""Tests for EP-1: Slide Note Playback (propeller.notes.Slide)."""
import pytest

from propeller.errors import PropellerValidationError


# ---------------------------------------------------------------------------
# T-1 to T-2: Slide construction
# ---------------------------------------------------------------------------

class TestSlideConstruction:
    def test_t1_fields_are_readable(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        assert s.start == C4
        assert s.end == C5
        assert s.steps == 0.1

    def test_t1_default_duration_is_one(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        assert s.duration == 1.0

    def test_t1_explicit_duration(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1, duration=2.0)
        assert s.duration == 2.0

    def test_t1_immutable(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        with pytest.raises(Exception):
            s.steps = 0.2


# ---------------------------------------------------------------------------
# T-3 to T-4: Slide construction validation
# ---------------------------------------------------------------------------

class TestSlideValidation:
    def test_t3_steps_zero_raises(self):
        from propeller.notes import Slide, C4, C5
        with pytest.raises(PropellerValidationError) as exc_info:
            Slide(C4, C5, steps=0)
        assert 'steps' in str(exc_info.value)

    def test_t3_steps_negative_raises(self):
        from propeller.notes import Slide, C4, C5
        with pytest.raises(PropellerValidationError):
            Slide(C4, C5, steps=-0.1)

    def test_t3_steps_above_one_raises(self):
        from propeller.notes import Slide, C4, C5
        with pytest.raises(PropellerValidationError):
            Slide(C4, C5, steps=1.1)

    def test_t3_steps_exactly_one_is_valid(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=1.0)
        assert s.steps == 1.0

    def test_t3_non_note_start_raises(self):
        from propeller.notes import Slide, C5
        with pytest.raises(PropellerValidationError) as exc_info:
            Slide(60, C5, steps=0.1)
        assert 'start' in str(exc_info.value) or 'Note' in str(exc_info.value)

    def test_t3_non_note_end_raises(self):
        from propeller.notes import Slide, C4
        with pytest.raises(PropellerValidationError):
            Slide(C4, 72, steps=0.1)

    def test_t3_equal_pitches_raises(self):
        from propeller.notes import Slide, C4
        with pytest.raises(PropellerValidationError) as exc_info:
            Slide(C4, C4, steps=0.1)
        assert 'pitch' in str(exc_info.value)

    def test_t3_raises_propeller_validation_error_not_value_error(self):
        from propeller.notes import Slide, C4, C5
        try:
            Slide(C4, C5, steps=0)
        except ValueError:
            pytest.fail("Should not raise plain ValueError")
        except PropellerValidationError:
            pass


# ---------------------------------------------------------------------------
# T-5 to T-6: Slide * n
# ---------------------------------------------------------------------------

class TestSlideMul:
    def test_t5_mul_returns_new_slide_with_updated_duration(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        result = s * 4
        assert result.duration == 4.0

    def test_t5_mul_preserves_original(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        _ = s * 4
        assert s.duration == 1.0

    def test_t5_mul_preserves_start_end_steps(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        result = s * 4
        assert result.start == C4
        assert result.end == C5
        assert result.steps == 0.1

    def test_t5_mul_float_duration(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        result = s * 0.5
        assert result.duration == 0.5

    def test_t5_mul_zero_raises_validation_error(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        with pytest.raises(PropellerValidationError) as exc_info:
            s * 0
        assert 'duration' in str(exc_info.value)

    def test_t5_mul_negative_raises_validation_error(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        with pytest.raises(PropellerValidationError):
            s * -1


# ---------------------------------------------------------------------------
# T-7 to T-8: Slide.intervals() whole-tone identification
# ---------------------------------------------------------------------------

class TestSlideIntervals:
    def test_t7_ascending_whole_number_of_tones_count(self):
        # AC-1: C4 -> C5 is 6 whole tones, so 6 intervals
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        intervals = s.intervals()
        assert len(intervals) == 6

    def test_t7_ascending_starting_pitches(self):
        # AC-1: intervals start at C4, D4, E4, Fs4, Gs4, As4
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        intervals = s.intervals()
        start_pitches = [i.start_pitch for i in intervals]
        assert start_pitches == [60, 62, 64, 66, 68, 70]

    def test_t7_ascending_ending_pitches(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        intervals = s.intervals()
        end_pitches = [i.end_pitch for i in intervals]
        assert end_pitches == [62, 64, 66, 68, 70, 72]

    def test_t7_ascending_all_full_tone_width(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1)
        intervals = s.intervals()
        assert all(i.tone_width == 1.0 for i in intervals)

    def test_t7_descending_count(self):
        # AC-8: C5 -> C4 also 6 whole tones
        from propeller.notes import Slide, C4, C5
        s = Slide(C5, C4, steps=0.1)
        intervals = s.intervals()
        assert len(intervals) == 6

    def test_t7_descending_starting_pitches(self):
        # AC-8: C5, As4, Gs4, Fs4, E4, D4
        from propeller.notes import Slide, C4, C5
        s = Slide(C5, C4, steps=0.1)
        intervals = s.intervals()
        start_pitches = [i.start_pitch for i in intervals]
        assert start_pitches == [72, 70, 68, 66, 64, 62]

    def test_t7_descending_final_end_pitch_is_c4(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C5, C4, steps=0.1)
        intervals = s.intervals()
        assert intervals[-1].end_pitch == 60

    def test_t7_non_whole_tone_two_intervals(self):
        # AC-5: C4 -> Ds4 (minor third, 1.5 tones): one full tone + one partial half-tone
        from propeller.notes import Slide, C4, Ds4
        s = Slide(C4, Ds4, steps=0.1)
        intervals = s.intervals()
        assert len(intervals) == 2

    def test_t7_non_whole_tone_first_interval_full_tone(self):
        from propeller.notes import Slide, C4, Ds4
        s = Slide(C4, Ds4, steps=0.1)
        intervals = s.intervals()
        assert intervals[0].start_pitch == 60
        assert intervals[0].end_pitch == 62
        assert intervals[0].tone_width == 1.0

    def test_t7_non_whole_tone_final_partial_interval(self):
        from propeller.notes import Slide, C4, Ds4
        s = Slide(C4, Ds4, steps=0.1)
        intervals = s.intervals()
        assert intervals[1].start_pitch == 62
        assert intervals[1].end_pitch == 63
        assert intervals[1].tone_width == 0.5


# ---------------------------------------------------------------------------
# T-9 to T-10: proportional time-share of each interval
# ---------------------------------------------------------------------------

class TestSlideIntervalTickLengths:
    def _tone_widths(self, tone_widths, total_duration_ticks):
        from propeller.serializer import _slide_interval_tick_lengths
        return _slide_interval_tick_lengths(tone_widths, total_duration_ticks)

    def test_t9_equal_widths_split_evenly(self):
        # AC-1: 6 equal 1.0-tone-wide intervals over 4 beats (1920 ticks) -> 320 each
        lengths = self._tone_widths([1.0] * 6, 1920)
        assert lengths == [320, 320, 320, 320, 320, 320]

    def test_t9_lengths_sum_to_total(self):
        lengths = self._tone_widths([1.0] * 6, 1920)
        assert sum(lengths) == 1920

    def test_t9_ac9_two_thirds_one_third_split(self):
        # AC-9: C4->Ds4 (1.5 tones total), duration 2 beats = 960 ticks.
        # Full-tone interval (1.0) lasts two-thirds (640), half-tone (0.5) lasts one-third (320).
        lengths = self._tone_widths([1.0, 0.5], 960)
        assert lengths == [640, 320]

    def test_t9_lengths_proportional_to_tone_width(self):
        lengths = self._tone_widths([1.0, 0.5], 960)
        assert lengths[0] == 2 * lengths[1]

    def test_t9_single_interval_gets_full_duration(self):
        lengths = self._tone_widths([0.5], 480)
        assert lengths == [480]


# ---------------------------------------------------------------------------
# T-11 to T-12: per-interval retriggered Note generation
# ---------------------------------------------------------------------------

class TestSlideNoteRows:
    def _note_rows(self, slide, start_tick=0, denominator=4):
        from propeller.serializer import _slide_note_rows
        return _slide_note_rows(slide, start_tick, denominator)

    def test_t11_ac1_produces_six_notes(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1) * 4
        rows = self._note_rows(s)
        assert len(rows) == 6

    def test_t11_ac1_note_pitches_are_interval_start_pitches(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1) * 4
        rows = self._note_rows(s)
        pitches = [r[2] for r in rows]
        assert pitches == [60, 62, 64, 66, 68, 70]

    def test_t11_ac1_each_note_lasts_one_sixth_of_total(self):
        # 4 beats at denom 4 -> 1920 ticks total -> 320 ticks per interval
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1) * 4
        rows = self._note_rows(s)
        assert all(r[1] == 320 for r in rows)

    def test_t11_notes_use_start_velocity_regardless_of_end_velocity(self):
        # AC-6
        from propeller.notes import Slide, C4, C5
        start = C4(80)
        end = C5(120)
        s = Slide(start, end, steps=0.1) * 4
        rows = self._note_rows(s)
        assert all(r[3] == 80 for r in rows)

    def test_t11_note_ticks_are_contiguous_from_start_tick(self):
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1) * 4
        rows = self._note_rows(s, start_tick=100)
        ticks = [r[0] for r in rows]
        assert ticks == [100, 420, 740, 1060, 1380, 1700]

    def test_t11_partial_final_interval_note(self):
        # AC-5: C4 -> Ds4 produces 2 notes: C4 and D4 (the partial interval's start pitch)
        from propeller.notes import Slide, C4, Ds4
        s = Slide(C4, Ds4, steps=0.1)
        rows = self._note_rows(s)
        pitches = [r[2] for r in rows]
        assert pitches == [60, 62]


# ---------------------------------------------------------------------------
# T-13 to T-14: per-interval pitch-bend value sequence
# ---------------------------------------------------------------------------

class TestSlidePitchBendValues:
    def _values(self, tone_width, steps, ascending=True):
        from propeller.serializer import _slide_pitch_bend_values
        return _slide_pitch_bend_values(tone_width, steps, ascending)

    def test_t13_ac2_full_tone_produces_ten_values(self):
        values = self._values(1.0, 0.1)
        assert len(values) == 10

    def test_t13_ac2_values_evenly_spaced_in_step_increments(self):
        values = self._values(1.0, 0.1)
        expected = [round(0.1 * i, 10) for i in range(1, 11)]
        assert [round(v, 10) for v in values] == expected

    def test_t13_ac2_last_value_equals_tone_width(self):
        # last pitch-bend event coincides with the next interval's starting pitch
        values = self._values(1.0, 0.1)
        assert values[-1] == pytest.approx(1.0)

    def test_t13_increments_no_larger_than_steps_when_evenly_divisible(self):
        values = self._values(1.0, 0.1)
        diffs = [values[0]] + [values[i] - values[i - 1] for i in range(1, len(values))]
        assert all(d <= 0.1 + 1e-9 for d in diffs)

    def test_t13_ac5_half_tone_partial_interval(self):
        # AC-5 second interval: 0.5 tone width, steps=0.1 -> 5 values ending at 0.5
        values = self._values(0.5, 0.1)
        assert len(values) == 5
        assert values[-1] == pytest.approx(0.5)

    def test_t13_ac7_non_evenly_dividing_steps_rounds_to_nearest(self):
        # AC-7: steps=0.3 does not evenly divide 1.0 tone; round(1.0/0.3) == 3
        values = self._values(1.0, 0.3)
        assert len(values) == 3

    def test_t13_ac7_last_value_still_equals_tone_width(self):
        values = self._values(1.0, 0.3)
        assert values[-1] == pytest.approx(1.0)

    def test_t13_descending_values_are_negative(self):
        # AC-8: descending slide produces negative pitch-bend values
        values = self._values(1.0, 0.1, ascending=False)
        assert len(values) == 10
        assert values[-1] == pytest.approx(-1.0)
        assert all(v <= 0 for v in values)

    def test_t13_no_validation_error_on_non_dividing_steps(self):
        # F-10: rounding absorbs the discrepancy rather than raising
        self._values(1.0, 0.3)  # must not raise


# ---------------------------------------------------------------------------
# T-15 to T-16: Track accepts Slide in a lane
# ---------------------------------------------------------------------------

class TestTrackWithSlide:
    def test_t15_single_lane_accepts_slide(self):
        from propeller.composition import Track
        from propeller.notes import Slide, C4, C5
        Track(name='Test', channel=1, instrument=0,
              notes=[Slide(C4, C5, steps=0.1) * 4])  # must not raise

    def test_t15_slide_alongside_note_and_rest(self):
        from propeller.composition import Track
        from propeller.notes import Slide, C4, C5, D4, Rest
        Track(name='Test', channel=1, instrument=0,
              notes=[D4, Rest(), Slide(C4, C5, steps=0.1) * 4])  # must not raise

    def test_t15_multi_lane_accepts_slide(self):
        from propeller.composition import Track
        from propeller.notes import Slide, C4, C5, E4, E5
        lane1 = [Slide(C4, C5, steps=0.1) * 4]
        lane2 = [Slide(E4, E5, steps=0.1) * 4]
        Track(name='Test', channel=1, instrument=0, notes=[lane1, lane2])  # must not raise

    def test_t15_slide_result_stored_on_track(self):
        from propeller.composition import Track
        from propeller.notes import Slide, C4, C5
        s = Slide(C4, C5, steps=0.1) * 4
        t = Track(name='Test', channel=1, instrument=0, notes=[s])
        assert t.notes[0] is s


# ---------------------------------------------------------------------------
# T-17 to T-18: full serialization of a Slide (worked example, briefing.md)
# ---------------------------------------------------------------------------

class TestSlideSerialization:
    """Slide(C4, C5, steps=0.1) * 4 in 4/4, 4 bars: the briefing's worked example."""

    def _serialize_worked_example(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, C5
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0,
                      notes=[Slide(C4, C5, steps=0.1) * 4])
        project = Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[track])
        return serialize(project)

    def test_t17_ac1_six_note_events(self):
        result = self._serialize_worked_example()
        notes_out = result['tracks'][0]['notes']
        assert len(notes_out) == 6

    def test_t17_ac1_note_pitches(self):
        result = self._serialize_worked_example()
        notes_out = result['tracks'][0]['notes']
        assert [n[2] for n in notes_out] == [60, 62, 64, 66, 68, 70]

    def test_t17_ac1_each_note_lasts_one_sixth_of_total_duration(self):
        # 4 beats @ 480 PPQN = 1920 ticks total -> 320 ticks per note
        result = self._serialize_worked_example()
        notes_out = result['tracks'][0]['notes']
        assert all(n[1] == 320 for n in notes_out)

    def test_t17_ac1_note_start_ticks(self):
        result = self._serialize_worked_example()
        notes_out = result['tracks'][0]['notes']
        assert [n[0] for n in notes_out] == [0, 320, 640, 960, 1280, 1600]

    def test_t17_note_velocities_default_to_start_note_velocity(self):
        result = self._serialize_worked_example()
        notes_out = result['tracks'][0]['notes']
        assert all(n[3] == 100 for n in notes_out)

    def test_t17_ac2_sixty_pitch_bend_events(self):
        # 6 intervals x 10 evenly-spaced pitch-bends each = 60, plus a leading
        # zero-reset at the slide's start tick (the trailing zero-reset
        # replaces rather than adds to the final ramp step, see below).
        result = self._serialize_worked_example()
        pbs = result['tracks'][0]['pitch-bends']
        assert len(pbs) == 61

    def test_t17_ac2_leading_pitch_bend_is_zero_reset(self):
        from propeller.serializer import _pb_to_int
        result = self._serialize_worked_example()
        pbs = result['tracks'][0]['pitch-bends']
        assert pbs[0] == [0, _pb_to_int(0.0)]

    def test_t17_ac2_first_interval_pitch_bend_ticks(self):
        result = self._serialize_worked_example()
        pbs = result['tracks'][0]['pitch-bends']
        # index 0 is the leading zero-reset; the first interval's ramp follows it
        first_interval_ticks = [pb[0] for pb in pbs[1:11]]
        assert first_interval_ticks == [32, 64, 96, 128, 160, 192, 224, 256, 288, 320]

    def test_t17_ac2_last_pb_of_interval_coincides_with_next_note_tick(self):
        result = self._serialize_worked_example()
        notes_out = result['tracks'][0]['notes']
        pbs = result['tracks'][0]['pitch-bends']
        # last PB of interval 1 (index 10, after the leading zero-reset)
        # should land on the same tick as note 2's start
        assert pbs[10][0] == notes_out[1][0]

    def test_t17_ac2_first_interval_pitch_bend_values(self):
        from propeller.serializer import _pb_to_int
        result = self._serialize_worked_example()
        pbs = result['tracks'][0]['pitch-bends']
        expected = [_pb_to_int(0.1 * i) for i in range(1, 11)]
        assert [pb[1] for pb in pbs[1:11]] == expected

    def test_t17_ac2_last_pb_is_zero_reset_not_full_tone_up(self):
        # The slide's end-tick reset to zero replaces what would otherwise
        # be the final ramp step (they land on the same tick, simultaneous
        # with the last retriggered note's note-off).
        from propeller.serializer import _pb_to_int
        result = self._serialize_worked_example()
        pbs = result['tracks'][0]['pitch-bends']
        assert pbs[-1] == [1920, _pb_to_int(0.0)]

    def test_t17_ac3_total_span_matches_duration(self):
        # 4 beats * 4 bars loop; slide spans exactly 1920 ticks (4 beats)
        result = self._serialize_worked_example()
        notes_out = result['tracks'][0]['notes']
        last_note_end = notes_out[-1][0] + notes_out[-1][1]
        assert last_note_end == 1920

    def test_t17_ac4_slide_position_among_other_notes(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, C5, D4
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0,
                      notes=[D4, Slide(C4, C5, steps=0.1) * 4, D4])
        project = Project(bpm=120, time_signature=(4, 4), bars=8, tracks=[track])
        result = serialize(project)
        notes_out = result['tracks'][0]['notes']
        # D4 (1 beat = 480 ticks), then 6 slide notes at 480 + [0,320,...,1600],
        # then trailing D4 at 480 + 1920 = 2400
        assert notes_out[0] == [0, 480, 62, 100]
        assert notes_out[1][0] == 480
        assert notes_out[-1] == [2400, 480, 62, 100]

    def test_t17_ac5_partial_final_interval_pitch_bend_count(self):
        # C4 -> Ds4: full tone interval (10 PBs) + half tone interval (5 PBs) = 15,
        # plus the leading zero-reset at the slide's start tick = 16.
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, Ds4
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0,
                      notes=[Slide(C4, Ds4, steps=0.1)])
        project = Project(bpm=120, time_signature=(4, 4), bars=1, tracks=[track])
        result = serialize(project)
        pbs = result['tracks'][0]['pitch-bends']
        assert len(pbs) == 16

    def test_t17_ac6_retriggered_notes_use_start_velocity_not_end(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, C5
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0,
                      notes=[Slide(C4(80), C5(120), steps=0.1) * 4])
        project = Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[track])
        result = serialize(project)
        notes_out = result['tracks'][0]['notes']
        assert all(n[3] == 80 for n in notes_out)

    def test_t17_ac8_descending_slide_pitch_order(self):
        from propeller.composition import Project, Track
        from propeller.notes import Slide, C4, C5
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0,
                      notes=[Slide(C5, C4, steps=0.1) * 4])
        project = Project(bpm=120, time_signature=(4, 4), bars=4, tracks=[track])
        result = serialize(project)
        notes_out = result['tracks'][0]['notes']
        assert [n[2] for n in notes_out] == [72, 70, 68, 66, 64, 62]

    def test_t17_nf1_deterministic_across_repeated_calls(self):
        result1 = self._serialize_worked_example()
        result2 = self._serialize_worked_example()
        assert result1 == result2

    def test_t17_serializer_does_not_touch_existing_note_pitch_bend_rest_handling(self):
        # Regression guard: a plain Note/Rest/PitchBend-only track still serializes
        # exactly as before Slide was introduced.
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
