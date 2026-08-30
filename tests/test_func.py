import pytest
from propeller.errors import PropellerValidationError
from propeller.func import probability, selection
from propeller.notes import Note, Rest, Slide, Z, to


class _FakeRng:
    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


class TestProbabilityOutcome:
    def test_below_threshold_returns_note(self):
        n = Note(60)
        result = probability(0.5, n, rng=_FakeRng(0.0))
        assert result is n

    def test_at_or_above_threshold_returns_replacement(self):
        n = Note(60)
        result = probability(0.5, n, rng=_FakeRng(0.5))
        assert result is Z

    def test_default_replacement_is_z(self):
        n = Note(60)
        result = probability(0.5, n, rng=_FakeRng(0.99))
        assert result is Z

    def test_custom_replacement(self):
        n = Note(60)
        r = Rest(duration=2.0)
        result = probability(0.5, n, replacement=r, rng=_FakeRng(0.99))
        assert result is r

    def test_probability_one_always_plays_note(self):
        n = Note(60)
        result = probability(1.0, n, rng=_FakeRng(0.999999))
        assert result is n

    def test_probability_zero_never_plays_note(self):
        n = Note(60)
        result = probability(0.0, n, rng=_FakeRng(0.0))
        assert result is Z


class TestProbabilityAcceptsSlide:
    def test_slide_below_threshold_returns_slide(self):
        s = Slide(Note(60), to(1.0))
        result = probability(0.5, s, rng=_FakeRng(0.0))
        assert result is s

    def test_slide_as_replacement(self):
        n = Note(60)
        s = Slide(Note(60), to(1.0))
        result = probability(0.5, n, replacement=s, rng=_FakeRng(0.99))
        assert result is s

    def test_mul_applies_to_played_slide(self):
        s = Slide(Note(60), to(1.0))
        result = probability(0.5, s, rng=_FakeRng(0.0)) * 2.0
        assert isinstance(result, Slide)
        assert result.duration == 2.0


class TestProbabilityComposability:
    def test_mul_applies_to_played_note(self):
        n = Note(60)
        result = probability(0.5, n, rng=_FakeRng(0.0)) * 0.5
        assert isinstance(result, Note)
        assert result.pitch == 60
        assert result.duration == 0.5

    def test_mul_applies_to_replacement(self):
        n = Note(60)
        result = probability(0.5, n, rng=_FakeRng(0.99)) * 0.5
        assert isinstance(result, Rest)
        assert result.duration == 0.5


class TestProbabilityValidation:
    def test_probability_above_one_raises(self):
        with pytest.raises(PropellerValidationError) as exc_info:
            probability(1.5, Note(60))
        assert 'probability' in str(exc_info.value)

    def test_probability_below_zero_raises(self):
        with pytest.raises(PropellerValidationError) as exc_info:
            probability(-0.1, Note(60))
        assert 'probability' in str(exc_info.value)

    def test_probability_wrong_type_raises(self):
        with pytest.raises(PropellerValidationError):
            probability('0.5', Note(60))  # type: ignore[arg-type]

    def test_note_wrong_type_raises(self):
        with pytest.raises(PropellerValidationError) as exc_info:
            probability(0.5, 'not a note')  # type: ignore[arg-type]
        assert 'note' in str(exc_info.value)

    def test_replacement_wrong_type_raises(self):
        with pytest.raises(PropellerValidationError) as exc_info:
            probability(0.5, Note(60), replacement='not a note')  # type: ignore[arg-type]
        assert 'replacement' in str(exc_info.value)

    def test_boundary_zero_is_valid(self):
        probability(0.0, Note(60), rng=_FakeRng(0.5))

    def test_boundary_one_is_valid(self):
        probability(1.0, Note(60), rng=_FakeRng(0.5))


class TestSelection:
    def test_before_matches_strictly_less_than(self):
        result = selection(4).before(5, 'a').after(5, 'b').select()
        assert result == 'a'

    def test_after_matches_greater_or_equal(self):
        result = selection(5).before(5, 'a').after(5, 'b').select()
        assert result == 'b'

    def test_last_matching_condition_wins(self):
        result = (
            selection(20)
            .after(5, 'a')
            .after(6, 'b')
            .after(20, 'c')
            .select()
        )
        assert result == 'c'

    def test_falls_back_to_default_when_nothing_matches(self):
        result = selection(10).before(5, 'a').default('fallback').select()
        assert result == 'fallback'

    def test_returns_none_when_nothing_matches_and_no_default(self):
        result = selection(10).before(5, 'a').select()
        assert result is None

    def test_value_can_be_any_type(self):
        result = selection(3).before(5, [1, 2, 3]).select()
        assert result == [1, 2, 3]

    def test_incomparable_threshold_raises(self):
        with pytest.raises(PropellerValidationError) as exc_info:
            selection(3).before('not-a-number', 'a')
        assert 'threshold' in str(exc_info.value)

    def test_returns_self_for_chaining(self):
        s = selection(1)
        assert s.before(5, 'a') is s
        assert s.after(5, 'b') is s
        assert s.default('c') is s
