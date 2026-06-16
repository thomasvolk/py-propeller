"""Tests for Epic 4: JSON Serialization (propeller/serializer.py)."""
import subprocess
import sys

import pytest

from propeller.notes import Rest
from tests.stubs import StubNote, StubProject, StubRest, StubTrack


# ---------------------------------------------------------------------------
# T-1: Stub domain model (tests/stubs.py)
# ---------------------------------------------------------------------------

class TestStubs:
    def test_stub_rest_isinstance_of_rest(self):
        sr = StubRest(duration=1.0)
        assert isinstance(sr, Rest)

    def test_stub_note_not_isinstance_of_rest(self):
        sn = StubNote(duration=1.0, pitch=60, velocity=100)
        assert not isinstance(sn, Rest)

    def test_stub_project_fields(self):
        sp = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[])
        assert sp.bpm == 120
        assert sp.time_signature == (4, 4)
        assert sp.bars == 1
        assert sp.tracks == []

    def test_stub_track_fields(self):
        st = StubTrack(name="Piano", channel=0, instrument=0, notes=[])
        assert st.name == "Piano"
        assert st.channel == 0
        assert st.instrument == 0
        assert st.notes == []

    def test_stub_note_fields(self):
        sn = StubNote(duration=2.0, pitch=60, velocity=80)
        assert sn.duration == 2.0
        assert sn.pitch == 60
        assert sn.velocity == 80

    def test_stub_rest_duration(self):
        sr = StubRest(duration=0.5)
        assert sr.duration == 0.5


# ---------------------------------------------------------------------------
# T-2: serialize() returns dict with "header" and "tracks", no "command"
# ---------------------------------------------------------------------------

class TestSerializeReturnShape:
    def _minimal_project(self):
        track = StubTrack(name="Piano", channel=0, instrument=0, notes=[])
        return StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[track])

    def test_returns_dict(self):
        from propeller.serializer import serialize
        result = serialize(self._minimal_project())
        assert isinstance(result, dict)

    def test_has_header_key(self):
        from propeller.serializer import serialize
        result = serialize(self._minimal_project())
        assert 'header' in result

    def test_has_tracks_key(self):
        from propeller.serializer import serialize
        result = serialize(self._minimal_project())
        assert 'tracks' in result

    def test_no_command_key(self):
        from propeller.serializer import serialize
        result = serialize(self._minimal_project())
        assert 'command' not in result


# ---------------------------------------------------------------------------
# T-3: header.bpm equals project.bpm
# ---------------------------------------------------------------------------

class TestHeaderBpm:
    def test_bpm_120(self):
        from propeller.serializer import serialize
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[])
        assert serialize(p)['header']['bpm'] == 120

    def test_bpm_140(self):
        from propeller.serializer import serialize
        p = StubProject(bpm=140, time_signature=(3, 4), bars=2, tracks=[])
        assert serialize(p)['header']['bpm'] == 140

    def test_bpm_arbitrary(self):
        from propeller.serializer import serialize
        p = StubProject(bpm=77, time_signature=(4, 4), bars=1, tracks=[])
        assert serialize(p)['header']['bpm'] == 77


# ---------------------------------------------------------------------------
# T-4: header.loop_duration = bars × beats_per_bar × 480
# ---------------------------------------------------------------------------

class TestHeaderLoopDuration:
    def test_bars1_ts44(self):
        from propeller.serializer import serialize
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[])
        assert serialize(p)['header']['loop_duration'] == 1920  # 1 × 4 × 480

    def test_bars3_ts44(self):
        from propeller.serializer import serialize
        p = StubProject(bpm=120, time_signature=(4, 4), bars=3, tracks=[])
        assert serialize(p)['header']['loop_duration'] == 5760  # 3 × 4 × 480

    def test_bars2_ts34(self):
        from propeller.serializer import serialize
        p = StubProject(bpm=120, time_signature=(3, 4), bars=2, tracks=[])
        assert serialize(p)['header']['loop_duration'] == 2880  # 2 × 3 × 480


# ---------------------------------------------------------------------------
# T-5: result["tracks"] has one entry per track with correct fields
# ---------------------------------------------------------------------------

class TestTracksStructure:
    def test_single_track_count(self):
        from propeller.serializer import serialize
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        assert len(serialize(p)['tracks']) == 1

    def test_two_tracks_count(self):
        from propeller.serializer import serialize
        t1 = StubTrack(name="Piano", channel=0, instrument=0, notes=[])
        t2 = StubTrack(name="Bass", channel=1, instrument=32, notes=[])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t1, t2])
        assert len(serialize(p)['tracks']) == 2

    def test_track_has_required_keys(self):
        from propeller.serializer import serialize
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        track_out = serialize(p)['tracks'][0]
        assert 'name' in track_out
        assert 'channel' in track_out
        assert 'instrument' in track_out
        assert 'notes' in track_out

    def test_track_name_value(self):
        from propeller.serializer import serialize
        t = StubTrack(name="Guitar", channel=2, instrument=25, notes=[])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        assert serialize(p)['tracks'][0]['name'] == 'Guitar'

    def test_track_channel_value(self):
        from propeller.serializer import serialize
        t1 = StubTrack(name="A", channel=0, instrument=0, notes=[])
        t2 = StubTrack(name="B", channel=1, instrument=0, notes=[])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t1, t2])
        tracks_out = serialize(p)['tracks']
        assert tracks_out[0]['channel'] == 1
        assert tracks_out[1]['channel'] == 2

    def test_track_instrument_value(self):
        from propeller.serializer import serialize
        t = StubTrack(name="Bass", channel=0, instrument=32, notes=[])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        assert serialize(p)['tracks'][0]['instrument'] == 32

    def test_empty_track_notes(self):
        from propeller.serializer import serialize
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        assert serialize(p)['tracks'][0]['notes'] == []


# ---------------------------------------------------------------------------
# T-6: single note maps to [start_tick, duration_ticks, pitch, velocity]
# ---------------------------------------------------------------------------

class TestSingleNoteMapping:
    def test_note_c4_velocity80_2beats(self):
        from propeller.serializer import serialize
        note = StubNote(duration=2, pitch=60, velocity=80)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=2, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out == [[0, 960, 60, 80]]

    def test_note_start_tick_is_zero(self):
        from propeller.serializer import serialize
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][0] == 0  # start_tick

    def test_note_duration_ticks_one_beat(self):
        from propeller.serializer import serialize
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][1] == 480  # duration_ticks


# ---------------------------------------------------------------------------
# T-7: two consecutive quarter notes get start_ticks 0 and 480
# ---------------------------------------------------------------------------

class TestConsecutiveNoteTicks:
    def test_two_quarter_notes_start_ticks(self):
        from propeller.serializer import serialize
        n1 = StubNote(duration=1, pitch=60, velocity=100)
        n2 = StubNote(duration=1, pitch=62, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[n1, n2])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][0] == 0
        assert notes_out[1][0] == 480

    def test_second_note_inherits_correct_tick(self):
        from propeller.serializer import serialize
        n1 = StubNote(duration=2, pitch=60, velocity=100)
        n2 = StubNote(duration=1, pitch=62, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[n1, n2])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=2, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[1][0] == 960  # 2 beats × 480


# ---------------------------------------------------------------------------
# T-8: rest advances cursor but produces no entry
# ---------------------------------------------------------------------------

class TestRestHandling:
    def test_rest_produces_no_note_entry(self):
        from propeller.serializer import serialize
        rest = StubRest(duration=1)
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[rest, note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert len(notes_out) == 1

    def test_rest_advances_start_tick(self):
        from propeller.serializer import serialize
        rest = StubRest(duration=1)
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[rest, note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][0] == 480  # start_tick after 1-beat rest

    def test_multiple_rests_accumulate(self):
        from propeller.serializer import serialize
        r1 = StubRest(duration=1)
        r2 = StubRest(duration=2)
        note = StubNote(duration=1, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[r1, r2, note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=4, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][0] == 1440  # (1+2) × 480


# ---------------------------------------------------------------------------
# T-9: fractional beat duration is rounded to nearest integer tick
# ---------------------------------------------------------------------------

class TestFractionalTickRounding:
    def test_triplet_duration(self):
        from propeller.serializer import serialize
        note = StubNote(duration=1 / 3, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        notes_out = serialize(p)['tracks'][0]['notes']
        assert notes_out[0][1] == round(1 / 3 * 480)  # 160

    def test_fractional_does_not_raise(self):
        from propeller.serializer import serialize
        note = StubNote(duration=1 / 3, pitch=60, velocity=100)
        t = StubTrack(name="Piano", channel=0, instrument=0, notes=[note])
        p = StubProject(bpm=120, time_signature=(4, 4), bars=1, tracks=[t])
        serialize(p)  # must not raise


# ---------------------------------------------------------------------------
# T-10: import in isolation (no socket, no engine)
# ---------------------------------------------------------------------------

class TestImportIsolation:
    def test_import_without_engine(self):
        result = subprocess.run(
            [sys.executable, '-c',
             'import propeller.serializer; '
             'assert callable(propeller.serializer.serialize)'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_no_transport_import(self):
        import propeller.serializer as serializer
        source_file = serializer.__file__
        with open(source_file) as f:
            source = f.read()
        assert 'propeller.transport' not in source
        assert 'from propeller.transport' not in source
