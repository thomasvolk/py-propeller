"""Tests for Epic 5: Play Loop & Script Lifecycle."""
import json
from unittest import mock

import pytest

from tests.stubs import StubNote, StubProject, StubRest, StubTrack


def _make_stub_project():
    track = StubTrack(
        name='lead',
        channel=1,
        instrument=1,
        notes=[StubNote(duration_beats=1.0, pitch=60, velocity=80)],
    )
    return StubProject(bpm=120, time_signature=(4, 4), bars=2, tracks=[track])


# ---------------------------------------------------------------------------
# T-1: play is importable and callable
# ---------------------------------------------------------------------------

class TestImport:
    def test_play_importable(self):
        from propeller.player import play
        assert callable(play)


# ---------------------------------------------------------------------------
# T-2: create-project command JSON shape
# ---------------------------------------------------------------------------

class TestCreateProjectCommand:
    def test_first_send_receives_create_project_json(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance
            # make loop exit immediately
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = [None, KeyboardInterrupt()]
                with pytest.raises(SystemExit):
                    play(project)

        calls = mock_instance.send.call_args_list
        first_payload = json.loads(calls[0][0][0])
        assert first_payload['command'] == 'create-project'
        assert 'header' in first_payload
        assert 'tracks' in first_payload

    def test_create_project_header_has_bpm(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = [None, KeyboardInterrupt()]
                with pytest.raises(SystemExit):
                    play(project)

        first_payload = json.loads(mock_instance.send.call_args_list[0][0][0])
        assert first_payload['header']['bpm'] == 120


# ---------------------------------------------------------------------------
# T-3: loop-start sent after successful create-project
# ---------------------------------------------------------------------------

class TestLoopStart:
    def test_second_send_receives_loop_start(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = [None, KeyboardInterrupt()]
                with pytest.raises(SystemExit):
                    play(project)

        calls = mock_instance.send.call_args_list
        assert len(calls) >= 2
        second_payload = json.loads(calls[1][0][0])
        assert second_payload == {'command': 'loop-start'}


# ---------------------------------------------------------------------------
# T-4: PropellerResponseError from create-project propagates; loop-start not sent
# ---------------------------------------------------------------------------

class TestCreateProjectError:
    def test_response_error_propagates(self):
        from propeller.player import play
        from propeller.errors import PropellerResponseError
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.send.side_effect = PropellerResponseError(code='bad_request')
            mock_client_cls.return_value = mock_instance
            with pytest.raises(PropellerResponseError):
                play(project)

    def test_send_called_exactly_once_on_response_error(self):
        from propeller.player import play
        from propeller.errors import PropellerResponseError
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.send.side_effect = PropellerResponseError(code='bad_request')
            mock_client_cls.return_value = mock_instance
            with pytest.raises(PropellerResponseError):
                play(project)

        assert mock_instance.send.call_count == 1


# ---------------------------------------------------------------------------
# T-5: blocking loop calls time.sleep; SystemExit eventually raised
# ---------------------------------------------------------------------------

class TestBlockingLoop:
    def test_sleep_called_and_systemexit_raised(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_client_cls.return_value = mock.MagicMock()
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = [None, KeyboardInterrupt()]
                with pytest.raises(SystemExit):
                    play(project)

        assert mock_time.sleep.call_count >= 1

    def test_sleep_called_with_positive_interval(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_client_cls.return_value = mock.MagicMock()
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = [KeyboardInterrupt()]
                with pytest.raises(SystemExit):
                    play(project)

        sleep_arg = mock_time.sleep.call_args[0][0]
        assert sleep_arg > 0


# ---------------------------------------------------------------------------
# T-6: KeyboardInterrupt → loop-stop sent, SystemExit(0) raised
# ---------------------------------------------------------------------------

class TestKeyboardInterruptShutdown:
    def test_systemexit_zero_on_keyboard_interrupt(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_client_cls.return_value = mock.MagicMock()
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with pytest.raises(SystemExit) as exc_info:
                    play(project)

        assert exc_info.value.code == 0

    def test_loop_stop_sent_on_keyboard_interrupt(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with pytest.raises(SystemExit):
                    play(project)

        calls = mock_instance.send.call_args_list
        last_payload = json.loads(calls[-1][0][0])
        assert last_payload == {'command': 'loop-stop'}


# ---------------------------------------------------------------------------
# T-7: loop-stop failure during shutdown is silently suppressed
# ---------------------------------------------------------------------------

class TestLoopStopFailureSuppressed:
    def test_systemexit_zero_even_when_loop_stop_fails(self):
        from propeller.player import play
        from propeller.errors import PropellerConnectionError
        project = _make_stub_project()

        send_calls = [None, None, PropellerConnectionError('engine gone')]

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.send.side_effect = send_calls
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with pytest.raises(SystemExit) as exc_info:
                    play(project)

        assert exc_info.value.code == 0

    def test_no_exception_propagates_when_loop_stop_fails(self):
        from propeller.player import play
        from propeller.errors import PropellerConnectionError
        project = _make_stub_project()

        send_calls = [None, None, PropellerConnectionError('engine gone')]

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.send.side_effect = send_calls
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                try:
                    play(project)
                except SystemExit:
                    pass  # expected

    def test_no_stderr_output_when_loop_stop_fails(self, capsys):
        from propeller.player import play
        from propeller.errors import PropellerConnectionError
        project = _make_stub_project()

        send_calls = [None, None, PropellerConnectionError('engine gone')]

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.send.side_effect = send_calls
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with pytest.raises(SystemExit):
                    play(project)

        captured = capsys.readouterr()
        assert captured.err == ''


# ---------------------------------------------------------------------------
# T-8: PropellerConnectionError from create-project propagates uncaught
# ---------------------------------------------------------------------------

class TestConnectionErrorPropagates:
    def test_connection_error_from_create_project_propagates(self):
        from propeller.player import play
        from propeller.errors import PropellerConnectionError
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.send.side_effect = PropellerConnectionError('no socket')
            mock_client_cls.return_value = mock_instance
            with pytest.raises(PropellerConnectionError):
                play(project)

    def test_connection_error_not_absorbed_as_systemexit(self):
        from propeller.player import play
        from propeller.errors import PropellerConnectionError
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.send.side_effect = PropellerConnectionError('no socket')
            mock_client_cls.return_value = mock_instance
            with pytest.raises(PropellerConnectionError):
                play(project)
            # if we reach here, SystemExit was NOT raised


# ---------------------------------------------------------------------------
# T-9: Project.play() delegates to propeller.player.play
# ---------------------------------------------------------------------------

class TestProjectPlayMethod:
    def test_play_method_exists(self):
        from propeller.composition import Project
        assert hasattr(Project, 'play')
        assert callable(Project.play)

    def test_play_delegates_to_player(self):
        from propeller.composition import Project
        from propeller.notes import Note
        project = Project(
            bpm=120,
            time_signature=(4, 4),
            bars=2,
            tracks=[],
        )
        with mock.patch('propeller.player.play') as mock_play:
            mock_play.return_value = None
            project.play()

        mock_play.assert_called_once_with(project)

    def test_play_delegates_with_correct_instance(self):
        from propeller.composition import Project
        project = Project(bpm=90, time_signature=(3, 4), bars=4, tracks=[])
        with mock.patch('propeller.player.play') as mock_play:
            mock_play.return_value = None
            project.play()

        assert mock_play.call_args[0][0] is project
