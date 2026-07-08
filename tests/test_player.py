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
        notes=[StubNote(duration=1.0, pitch=60, velocity=80)],
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


# ---------------------------------------------------------------------------
# T-10: dry-run mode (-n flag)
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_prints_two_json_lines(self, capsys):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            with mock.patch('sys.argv', ['script.py', '-n']):
                play(project)

        captured = capsys.readouterr()
        lines = [l for l in captured.out.splitlines() if l.strip()]
        assert len(lines) == 2
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first['command'] == 'create-project'
        assert 'header' in first
        assert 'tracks' in first
        assert second == {'command': 'loop-start'}

    def test_dry_run_no_socket_opened(self, capsys):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            with mock.patch('sys.argv', ['script.py', '-n']):
                play(project)

        mock_client_cls.assert_not_called()

    def test_dry_run_returns_immediately(self, capsys):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient'):
            with mock.patch('propeller.player.time') as mock_time:
                with mock.patch('sys.argv', ['script.py', '-n']):
                    play(project)

        mock_time.sleep.assert_not_called()

    def test_live_mode_unaffected_when_no_flag(self, capsys):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_client_cls.return_value = mock.MagicMock()
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with mock.patch('sys.argv', ['script.py']):
                    with pytest.raises(SystemExit):
                        play(project)

        assert mock_client_cls.called


# ---------------------------------------------------------------------------
# T-11: -s inactive sends loop-stop and returns immediately (no blocking)
# ---------------------------------------------------------------------------

class TestStateInactive:
    def test_sends_loop_stop(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance
            with mock.patch('sys.argv', ['script.py', '-s', 'inactive']):
                with pytest.raises(SystemExit):
                    play(project)

        calls = mock_instance.send.call_args_list
        assert len(calls) == 1
        payload = json.loads(calls[0][0][0])
        assert payload == {'command': 'loop-stop'}

    def test_exits_immediately_with_code_zero(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_client_cls.return_value = mock.MagicMock()
            with mock.patch('sys.argv', ['script.py', '-s', 'inactive']):
                with pytest.raises(SystemExit) as exc_info:
                    play(project)

        assert exc_info.value.code == 0

    def test_no_serialization_occurs(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.serialize') as mock_serialize:
                with mock.patch('sys.argv', ['script.py', '-s', 'inactive']):
                    with pytest.raises(SystemExit):
                        play(project)

        mock_serialize.assert_not_called()


# ---------------------------------------------------------------------------
# T-12: -s active, project_present=False → create-project + loop-start, returns
# ---------------------------------------------------------------------------

class TestStateActiveNoProject:
    def test_sends_create_project_then_loop_start(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.query.return_value = {'status': 'ok', 'project_present': False}
            mock_client_cls.return_value = mock_instance
            with mock.patch('sys.argv', ['script.py', '-s', 'active']):
                with pytest.raises(SystemExit):
                    play(project)

        send_calls = mock_instance.send.call_args_list
        assert len(send_calls) == 2
        first = json.loads(send_calls[0][0][0])
        second = json.loads(send_calls[1][0][0])
        assert first['command'] == 'create-project'
        assert 'header' in first
        assert 'tracks' in first
        assert second == {'command': 'loop-start'}

    def test_exits_immediately_with_code_zero(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.query.return_value = {'status': 'ok', 'project_present': False}
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                with mock.patch('sys.argv', ['script.py', '-s', 'active']):
                    with pytest.raises(SystemExit) as exc_info:
                        play(project)

        assert exc_info.value.code == 0
        mock_time.sleep.assert_not_called()


# ---------------------------------------------------------------------------
# T-13: -s active, project_present=True → modify-project + loop-start, returns
# ---------------------------------------------------------------------------

class TestStateActiveWithProject:
    def test_sends_modify_project_then_loop_start(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.query.return_value = {'status': 'ok', 'project_present': True}
            mock_client_cls.return_value = mock_instance
            with mock.patch('sys.argv', ['script.py', '-s', 'active']):
                with pytest.raises(SystemExit):
                    play(project)

        send_calls = mock_instance.send.call_args_list
        assert len(send_calls) == 2
        first = json.loads(send_calls[0][0][0])
        second = json.loads(send_calls[1][0][0])
        assert first['command'] == 'modify-project'
        assert 'header' in first
        assert 'tracks' in first
        assert second == {'command': 'loop-start'}

    def test_modify_project_same_payload_shape_as_create(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance

            mock_instance.query.return_value = {'status': 'ok', 'project_present': False}
            with mock.patch('sys.argv', ['script.py', '-s', 'active']):
                with pytest.raises(SystemExit):
                    play(project)
            create_payload = json.loads(mock_instance.send.call_args_list[0][0][0])

            mock_instance.reset_mock()
            mock_instance.query.return_value = {'status': 'ok', 'project_present': True}
            with mock.patch('sys.argv', ['script.py', '-s', 'active']):
                with pytest.raises(SystemExit):
                    play(project)
            modify_payload = json.loads(mock_instance.send.call_args_list[0][0][0])

        assert set(create_payload.keys()) == set(modify_payload.keys())
        assert create_payload['header'] == modify_payload['header']
        assert create_payload['tracks'] == modify_payload['tracks']

    def test_exits_immediately_with_code_zero(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_instance.query.return_value = {'status': 'ok', 'project_present': True}
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                with mock.patch('sys.argv', ['script.py', '-s', 'active']):
                    with pytest.raises(SystemExit) as exc_info:
                        play(project)

        assert exc_info.value.code == 0
        mock_time.sleep.assert_not_called()


# ---------------------------------------------------------------------------
# T-14: -n and -s active together → dry-run takes precedence
# ---------------------------------------------------------------------------

class TestDryRunPrecedenceOverStateActive:
    def test_dry_run_output_not_socket(self, capsys):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            with mock.patch('sys.argv', ['script.py', '-n', '-s', 'active']):
                play(project)

        mock_client_cls.assert_not_called()
        captured = capsys.readouterr()
        lines = [l for l in captured.out.splitlines() if l.strip()]
        assert len(lines) == 2
        assert json.loads(lines[0])['command'] == 'create-project'
        assert json.loads(lines[1]) == {'command': 'loop-start'}


# ---------------------------------------------------------------------------
# T-15: -n and -s inactive together → dry-run takes precedence
# ---------------------------------------------------------------------------

class TestDryRunPrecedenceOverStateInactive:
    def test_dry_run_output_not_socket(self, capsys):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            with mock.patch('sys.argv', ['script.py', '-n', '-s', 'inactive']):
                play(project)

        mock_client_cls.assert_not_called()
        captured = capsys.readouterr()
        lines = [l for l in captured.out.splitlines() if l.strip()]
        assert len(lines) == 2
        assert json.loads(lines[0])['command'] == 'create-project'
        assert json.loads(lines[1]) == {'command': 'loop-start'}


# ---------------------------------------------------------------------------
# T-1/T-2: -s sync sends create-project only, exits immediately, no blocking
# ---------------------------------------------------------------------------

class TestStateSync:
    def test_sends_create_project_only(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with mock.patch('sys.argv', ['script.py', '-s', 'sync']):
                    with pytest.raises(SystemExit):
                        play(project)

        send_calls = mock_instance.send.call_args_list
        assert len(send_calls) == 1
        payload = json.loads(send_calls[0][0][0])
        assert payload['command'] == 'create-project'
        assert 'header' in payload
        assert 'tracks' in payload

    def test_no_loop_start_or_loop_stop_sent(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_instance = mock.MagicMock()
            mock_client_cls.return_value = mock_instance
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with mock.patch('sys.argv', ['script.py', '-s', 'sync']):
                    with pytest.raises(SystemExit):
                        play(project)

        send_calls = mock_instance.send.call_args_list
        for call in send_calls:
            payload = json.loads(call[0][0])
            assert payload.get('command') not in ('loop-start', 'loop-stop')

    def test_exits_immediately_with_code_zero(self):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            mock_client_cls.return_value = mock.MagicMock()
            with mock.patch('propeller.player.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with mock.patch('sys.argv', ['script.py', '-s', 'sync']):
                    with pytest.raises(SystemExit) as exc_info:
                        play(project)

        assert exc_info.value.code == 0
        mock_time.sleep.assert_not_called()


# ---------------------------------------------------------------------------
# T-4: -n and -s sync together → dry-run takes precedence
# ---------------------------------------------------------------------------

class TestDryRunPrecedenceOverStateSync:
    def test_dry_run_output_not_socket(self, capsys):
        from propeller.player import play
        project = _make_stub_project()

        with mock.patch('propeller.player.PropellerClient') as mock_client_cls:
            with mock.patch('sys.argv', ['script.py', '-n', '-s', 'sync']):
                play(project)

        mock_client_cls.assert_not_called()
        captured = capsys.readouterr()
        lines = [l for l in captured.out.splitlines() if l.strip()]
        assert len(lines) == 2
        assert json.loads(lines[0])['command'] == 'create-project'
        assert json.loads(lines[1]) == {'command': 'loop-start'}
