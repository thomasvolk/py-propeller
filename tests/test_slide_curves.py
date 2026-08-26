"""Tests for the sin/cos/gauss/custom Slide curve generators
(propeller.notes.Slide), per specs/briefing.md."""
import math

import pytest

from propeller.errors import PropellerValidationError


# ---------------------------------------------------------------------------
# SlideCurve construction / validation
# ---------------------------------------------------------------------------

class TestSlideCurveConstruction:
    def test_func_is_stored(self):
        from propeller.notes.Slide import SlideCurve
        func = lambda p: p
        curve = SlideCurve(func)
        assert curve.func is func

    def test_steps_defaults_to_point_zero_one(self):
        from propeller.notes.Slide import SlideCurve
        curve = SlideCurve(lambda p: p)
        assert curve.steps == 0.01

    def test_explicit_steps(self):
        from propeller.notes.Slide import SlideCurve
        curve = SlideCurve(lambda p: p, steps=0.05)
        assert curve.steps == 0.05

    def test_non_callable_func_raises(self):
        from propeller.notes.Slide import SlideCurve
        with pytest.raises(PropellerValidationError):
            SlideCurve(1.0)

    def test_steps_zero_raises(self):
        from propeller.notes.Slide import SlideCurve
        with pytest.raises(PropellerValidationError):
            SlideCurve(lambda p: p, steps=0)

    def test_steps_above_one_raises(self):
        from propeller.notes.Slide import SlideCurve
        with pytest.raises(PropellerValidationError):
            SlideCurve(lambda p: p, steps=1.1)

    def test_value_at_delegates_to_func(self):
        from propeller.notes.Slide import SlideCurve
        curve = SlideCurve(lambda p: p * 2)
        assert curve.value_at(0.25) == pytest.approx(0.5)

    def test_immutable(self):
        from propeller.notes.Slide import SlideCurve
        curve = SlideCurve(lambda p: p)
        with pytest.raises(Exception):
            curve.steps = 0.5


# ---------------------------------------------------------------------------
# sin / cos
# ---------------------------------------------------------------------------

class TestSinCos:
    def test_sin_defaults(self):
        from propeller.notes.Slide import sin, SlideCurve
        curve = sin()
        assert isinstance(curve, SlideCurve)
        assert curve.steps == 0.01

    def test_sin_default_amp_is_two(self):
        # amp defaults to 2 (the range statement in the doc was the typo,
        # per clarification), so the raw wave spans [-2, 2] before clipping.
        from propeller.notes.Slide import sin
        curve = sin(period=2)
        assert curve.func(0.25) == pytest.approx(2.0)

    def test_sin_formula(self):
        from propeller.notes.Slide import sin
        curve = sin(amp=1, period=2, y_offset=0)
        for p in (0.0, 0.1, 0.25, 0.5, 0.9, 1.0):
            expected = 1 * math.sin(p * 2 * math.pi) + 0
            assert curve.func(p) == pytest.approx(expected)

    def test_sin_y_offset_shifts_wave(self):
        from propeller.notes.Slide import sin
        curve = sin(amp=1, period=2, y_offset=1)
        assert curve.func(0.0) == pytest.approx(1.0)  # sin(0)=0, +1
        assert curve.func(0.75) == pytest.approx(0.0)  # sin(3pi/2)=-1, +1

    def test_cos_formula(self):
        from propeller.notes.Slide import cos
        curve = cos(amp=1, period=2, y_offset=0)
        for p in (0.0, 0.1, 0.25, 0.5, 0.9, 1.0):
            expected = 1 * math.cos(p * 2 * math.pi) + 0
            assert curve.func(p) == pytest.approx(expected)

    def test_cos_starts_at_amp_plus_offset(self):
        from propeller.notes.Slide import cos
        curve = cos(amp=1, period=2, y_offset=0)
        assert curve.func(0.0) == pytest.approx(1.0)  # cos(0) == 1


# ---------------------------------------------------------------------------
# gauss
# ---------------------------------------------------------------------------

class TestGauss:
    def test_gauss_defaults(self):
        from propeller.notes.Slide import gauss, SlideCurve
        curve = gauss()
        assert isinstance(curve, SlideCurve)
        assert curve.steps == 0.01

    def test_gauss_peaks_at_midpoint(self):
        from propeller.notes.Slide import gauss
        curve = gauss(u=0, o=1)
        assert curve.func(0.5) == pytest.approx(1.0)

    def test_gauss_near_zero_at_start_and_end(self):
        from propeller.notes.Slide import gauss
        curve = gauss(u=0, o=1)
        assert curve.func(0.0) < 0.02
        assert curve.func(1.0) < 0.02

    def test_gauss_symmetric(self):
        from propeller.notes.Slide import gauss
        curve = gauss(u=0, o=1)
        assert curve.func(0.2) == pytest.approx(curve.func(0.8))

    def test_gauss_monotonic_rise_then_fall(self):
        from propeller.notes.Slide import gauss
        curve = gauss(u=0, o=1)
        values = [curve.func(p / 20) for p in range(21)]
        rising = values[:11]
        falling = values[10:]
        assert rising == sorted(rising)
        assert falling == sorted(falling, reverse=True)


# ---------------------------------------------------------------------------
# custom function as Slide target
# ---------------------------------------------------------------------------

class TestCustomCurve:
    def test_plain_function_accepted_as_target(self):
        from propeller.notes import Slide, C4

        def my_func(ctx):
            return ctx

        s = Slide(C4, my_func)
        assert s.target is my_func

    def test_lambda_accepted_as_target(self):
        from propeller.notes import Slide, C4
        s = Slide(C4, lambda ctx: 0.5)
        assert callable(s.target)

    def test_note_instance_still_rejected_as_target(self):
        # Note defines __call__ (for the velocity syntax C4(80)), so the
        # custom-function acceptance must not accidentally treat a bare
        # Note as a valid curve.
        from propeller.notes import Slide, C4, D4
        with pytest.raises(PropellerValidationError):
            Slide(C4, D4)

    def test_pitch_bend_instance_rejected_as_target(self):
        # PitchBend also defines __call__ and must be excluded the same way.
        from propeller.notes import Slide, C4, PB
        with pytest.raises(PropellerValidationError):
            Slide(C4, PB(0.5))

    def test_custom_ctx_is_progress_fraction(self):
        from propeller.serializer import _expand_slide
        from propeller.notes import Slide, C4

        seen = []

        def my_func(ctx):
            seen.append(ctx)
            return 0.0

        s = Slide(C4, my_func) * 4
        _expand_slide(s, 0)
        assert seen[0] == pytest.approx(0.01)
        assert seen[-1] == pytest.approx(1.0)
        assert len(seen) == 100  # default steps=0.01 -> round(1/0.01)


# ---------------------------------------------------------------------------
# end-to-end: curves through _expand_slide / serialize, including clipping
# ---------------------------------------------------------------------------

class TestCurveSerialization:
    def _serialize(self, note, target, beats=4, bars=4):
        from propeller.composition import Project, Track
        from propeller.notes import Slide
        from propeller.serializer import serialize
        track = Track(name='Lead', channel=1, instrument=0,
                      notes=[Slide(note, target) * beats])
        project = Project(bpm=120, time_signature=(4, 4), bars=bars, tracks=[track])
        return serialize(project)

    def test_sin_default_amp_clips_to_valid_range(self):
        # amp defaults to 2, so the raw wave reaches +/-2 and must be
        # clipped to the pitch-bend range [-1.0, 1.0].
        from propeller.notes.Slide import sin
        from propeller.notes import C4
        from propeller.serializer import _pb_to_int
        result = self._serialize(C4, sin(period=2, steps=0.25))
        pbs = result['tracks'][0]['pitch-bends']
        values = [pb[1] for pb in pbs]
        assert max(values) == _pb_to_int(1.0)
        assert min(values) == _pb_to_int(-1.0)

    def test_amp_one_y_offset_one_clips_to_zero_one_range(self):
        # briefing worked example: amp=1, y_offset=1 -> wave between 0 and 1
        # (raw range is [0, 2]; only the upper bound needs clipping).
        from propeller.notes.Slide import sin
        from propeller.notes import C4
        from propeller.serializer import _pb_to_int
        result = self._serialize(C4, sin(amp=1, period=2, y_offset=1, steps=0.05))
        pbs = result['tracks'][0]['pitch-bends']
        values = [pb[1] for pb in pbs]
        assert max(values) == _pb_to_int(1.0)
        assert min(values) >= _pb_to_int(0.0)

    def test_gauss_end_to_end_reaches_near_peak(self):
        from propeller.notes.Slide import gauss
        from propeller.notes import C4
        from propeller.serializer import _pb_to_int
        result = self._serialize(C4, gauss(steps=0.1))
        pbs = result['tracks'][0]['pitch-bends']
        values = [pb[1] for pb in pbs]
        assert max(values) == pytest.approx(_pb_to_int(1.0), abs=1)

    def test_custom_function_end_to_end(self):
        from propeller.notes import C4
        from propeller.serializer import _pb_to_int

        def half(ctx):
            return 0.5

        result = self._serialize(C4, half, beats=1, bars=1)
        pbs = result['tracks'][0]['pitch-bends']
        # leading zero-reset, then ramp values all at 0.5, trailing zero-reset
        assert pbs[0][1] == _pb_to_int(0.0)
        assert pbs[1][1] == _pb_to_int(0.5)
        assert pbs[-1][1] == _pb_to_int(0.0)

    def test_to_still_works_unchanged_alongside_curves(self):
        # regression guard: to() keeps working as the linear special case
        from propeller.notes.Slide import to
        from propeller.notes import C4
        result = self._serialize(C4, to(1.0, steps=0.01))
        notes_out = result['tracks'][0]['notes']
        pbs = result['tracks'][0]['pitch-bends']
        assert notes_out == [[0, 1920, 60, 100]]
        assert len(pbs) == 101
