"""Tests for EP-1: Time Signature Governs Bar Length (specs/EP-1.md)."""
import json
from unittest import mock

from propeller.composition import Project, Track
from propeller.notes import C4
from tests.stubs import StubNote, StubProject, StubTrack


# ---------------------------------------------------------------------------
# T-1: unit-duration note under (4, 4) serializes to 480 ticks (quarter note)
# ---------------------------------------------------------------------------

class TestUnitDurationTicksTimeSignature44:
    def test_unit_duration_is_quarter_note_ticks(self):
        from propeller.serializer import serialize
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=1, instrument=0, notes=[note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][1] == 480


# ---------------------------------------------------------------------------
# T-2: unit-duration note under (8, 8) serializes to 240 ticks (eighth note)
# ---------------------------------------------------------------------------

class TestUnitDurationTicksTimeSignature88:
    def test_unit_duration_is_eighth_note_ticks(self):
        from propeller.serializer import serialize
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=1, instrument=0, notes=[note])
        p = StubProject(bpm=120, time_signature=(8, 8), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][1] == 240


# ---------------------------------------------------------------------------
# T-3: unit-duration note under (numerator, 16) serializes to 120 ticks
#      (sixteenth note), confirming the 4/denominator formula generalizes
# ---------------------------------------------------------------------------

class TestUnitDurationTicksGeneralizesToSixteenth:
    def test_unit_duration_is_sixteenth_note_ticks(self):
        from propeller.serializer import serialize
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=1, instrument=0, notes=[note])
        p = StubProject(bpm=120, time_signature=(4, 16), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][1] == 120


# ---------------------------------------------------------------------------
# T-4..T-7: numerator consecutive unit-duration notes exactly fill one bar
# ---------------------------------------------------------------------------

class TestNotesExactlyFillOneBar:
    def _bar_span(self, time_signature, note_count):
        from propeller.serializer import serialize
        track = Track(
            name="Piano", channel=1, instrument=0,
            notes=[C4 * 1 for _ in range(note_count)],
        )
        project = Project(bpm=120, time_signature=time_signature, bars=1, tracks=[track])
        result = serialize(project)
        notes_out = result['tracks'][0]['notes']
        last_start, last_duration, _, _ = notes_out[-1]
        span = last_start + last_duration
        return span, result['header']['loop_duration']

    def test_ts_4_4_four_quarter_notes_fill_one_bar(self):
        span, loop_duration = self._bar_span((4, 4), 4)
        assert span == loop_duration == 1920

    def test_ts_8_8_eight_eighth_notes_fill_one_bar(self):
        span, loop_duration = self._bar_span((8, 8), 8)
        assert span == loop_duration == 1920

    def test_ts_4_8_four_eighth_notes_fill_one_bar(self):
        span, loop_duration = self._bar_span((4, 8), 4)
        assert span == loop_duration == 960

    def test_ts_8_4_eight_quarter_notes_fill_one_bar(self):
        span, loop_duration = self._bar_span((8, 4), 8)
        assert span == loop_duration == 3840


# ---------------------------------------------------------------------------
# T-8: two otherwise-identical projects differing only in time_signature
#      produce different serialized tick output
# ---------------------------------------------------------------------------

class TestTimeSignatureChangesSerializedOutput:
    def _serialized(self, time_signature):
        from propeller.serializer import serialize
        track = Track(name="Piano", channel=1, instrument=0, notes=[C4 * 1, C4 * 1])
        project = Project(bpm=120, time_signature=time_signature, bars=1, tracks=[track])
        return serialize(project)

    def test_changing_time_signature_changes_output(self):
        result_44 = self._serialized((4, 4))
        result_48 = self._serialized((4, 8))
        assert result_44 != result_48
        assert result_44['header']['loop_duration'] != result_48['header']['loop_duration']
        assert result_44['tracks'][0]['notes'] != result_48['tracks'][0]['notes']


# ---------------------------------------------------------------------------
# T-9: bars stays purely informational — no validation against note content
# ---------------------------------------------------------------------------

class TestBarsRemainsInformationalOnly:
    def test_overfilled_bar_does_not_raise(self):
        from propeller.serializer import serialize
        # time_signature=(3, 8) means 1 bar = 3 eighth-note beats; 5 beats overfills it.
        track = Track(name="Piano", channel=1, instrument=0, notes=[C4 * 5])
        project = Project(bpm=120, time_signature=(3, 8), bars=1, tracks=[track])
        serialize(project)  # must not raise

    def test_underfilled_bar_does_not_raise(self):
        from propeller.serializer import serialize
        track = Track(name="Piano", channel=1, instrument=0, notes=[C4 * 1])
        project = Project(bpm=120, time_signature=(3, 8), bars=2, tracks=[track])
        serialize(project)  # must not raise


# ---------------------------------------------------------------------------
# T-10: player.py dry-run output under a non-(4, 4) time signature matches
#       a direct serialize() call — no independent playback timing path
# ---------------------------------------------------------------------------

class TestPlayerDryRunMatchesSerializerUnderNonDefaultTimeSignature:
    def test_dry_run_output_matches_serialize(self, capsys):
        from propeller.player import play
        from propeller.serializer import serialize
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=1, instrument=0, notes=[note])
        project = StubProject(bpm=120, time_signature=(8, 8), bars=1, tracks=[t])

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            with mock.patch('sys.argv', ['script.py', '-n']):
                play(project)

        mock_client_cls.assert_not_called()
        captured = capsys.readouterr()
        printed = json.loads(captured.out.strip())
        assert printed == serialize(project)
