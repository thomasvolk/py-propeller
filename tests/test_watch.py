"""Tests for the py-propeller watcher (propeller/watch.py)."""
import json
from unittest import mock

import pytest


# ---------------------------------------------------------------------------
# main is importable and callable
# ---------------------------------------------------------------------------

class TestImport:
    def test_main_importable(self):
        from propeller.watch import main
        assert callable(main)


# ---------------------------------------------------------------------------
# argument parsing
# ---------------------------------------------------------------------------

class TestArgParsing:
    def test_script_is_required(self):
        from propeller.watch import _parse_args
        with pytest.raises(SystemExit):
            _parse_args([])

    def test_script_path_captured(self, tmp_path):
        from propeller.watch import _parse_args
        script = tmp_path / 'example.py'
        script.write_text('')
        args = _parse_args([str(script)])
        assert args.script == str(script)

    def test_default_interval_is_100ms(self, tmp_path):
        from propeller.watch import _parse_args
        script = tmp_path / 'example.py'
        script.write_text('')
        args = _parse_args([str(script)])
        assert args.interval_ms == 100

    def test_custom_interval_via_n_flag(self, tmp_path):
        from propeller.watch import _parse_args
        script = tmp_path / 'example.py'
        script.write_text('')
        args = _parse_args([str(script), '-n', '250'])
        assert args.interval_ms == 250

    def test_non_positive_interval_rejected(self, tmp_path):
        from propeller.watch import _parse_args
        script = tmp_path / 'example.py'
        script.write_text('')
        with pytest.raises(SystemExit):
            _parse_args([str(script), '-n', '0'])

    def test_missing_script_file_rejected(self, tmp_path):
        from propeller.watch import _parse_args
        missing = tmp_path / 'does_not_exist.py'
        with pytest.raises(SystemExit):
            _parse_args([str(missing)])

    def test_default_state_is_active(self, tmp_path):
        from propeller.watch import _parse_args
        script = tmp_path / 'example.py'
        script.write_text('')
        args = _parse_args([str(script)])
        assert args.state == 'active'

    def test_custom_state_via_s_flag(self, tmp_path):
        from propeller.watch import _parse_args
        script = tmp_path / 'example.py'
        script.write_text('')
        args = _parse_args([str(script), '-s', 'sync'])
        assert args.state == 'sync'

    def test_inactive_state_via_s_flag(self, tmp_path):
        from propeller.watch import _parse_args
        script = tmp_path / 'example.py'
        script.write_text('')
        args = _parse_args([str(script), '-s', 'inactive'])
        assert args.state == 'inactive'

    def test_invalid_state_rejected(self, tmp_path):
        from propeller.watch import _parse_args
        script = tmp_path / 'example.py'
        script.write_text('')
        with pytest.raises(SystemExit):
            _parse_args([str(script), '-s', 'bogus'])


# ---------------------------------------------------------------------------
# _run_once: forces sys.argv to "-s active", restores it, isolates errors
# ---------------------------------------------------------------------------

class TestRunOnce:
    def test_forces_s_active_argv(self, tmp_path):
        from propeller.watch import _run_once
        import sys
        script = str(tmp_path / 'example.py')
        seen_argv = []

        def _capture_argv(*_args, **_kwargs):
            seen_argv.append(list(sys.argv))

        with mock.patch('propeller.watch.runpy') as mock_runpy:
            mock_runpy.run_path.side_effect = _capture_argv
            _run_once(script)

        assert seen_argv == [[script, '-s', 'active']]

    def test_forwards_custom_state_argv(self, tmp_path):
        from propeller.watch import _run_once
        import sys
        script = str(tmp_path / 'example.py')
        seen_argv = []

        def _capture_argv(*_args, **_kwargs):
            seen_argv.append(list(sys.argv))

        with mock.patch('propeller.watch.runpy') as mock_runpy:
            mock_runpy.run_path.side_effect = _capture_argv
            _run_once(script, 'sync')

        assert seen_argv == [[script, '-s', 'sync']]

    def test_restores_original_argv_after(self, tmp_path):
        from propeller.watch import _run_once
        import sys
        script = str(tmp_path / 'example.py')
        original = list(sys.argv)

        with mock.patch('propeller.watch.runpy'):
            _run_once(script)

        assert sys.argv == original

    def test_restores_argv_even_on_exception(self, tmp_path):
        from propeller.watch import _run_once
        import sys
        script = str(tmp_path / 'example.py')
        original = list(sys.argv)

        with mock.patch('propeller.watch.runpy') as mock_runpy:
            mock_runpy.run_path.side_effect = ValueError('boom')
            _run_once(script)

        assert sys.argv == original

    def test_system_exit_zero_is_silent(self, tmp_path, capsys):
        from propeller.watch import _run_once
        script = str(tmp_path / 'example.py')

        with mock.patch('propeller.watch.runpy') as mock_runpy:
            mock_runpy.run_path.side_effect = SystemExit(0)
            _run_once(script)

        captured = capsys.readouterr()
        assert captured.err == ''

    def test_exception_is_logged_not_raised(self, tmp_path, capsys):
        from propeller.watch import _run_once
        script = str(tmp_path / 'example.py')

        with mock.patch('propeller.watch.runpy') as mock_runpy:
            mock_runpy.run_path.side_effect = ValueError('bad syntax edit')
            _run_once(script)  # must not raise

        captured = capsys.readouterr()
        assert 'ValueError' in captured.err
        assert 'bad syntax edit' in captured.err

    def test_nonzero_system_exit_is_logged(self, tmp_path, capsys):
        from propeller.watch import _run_once
        script = str(tmp_path / 'example.py')

        with mock.patch('propeller.watch.runpy') as mock_runpy:
            mock_runpy.run_path.side_effect = SystemExit(1)
            _run_once(script)  # must not raise

        captured = capsys.readouterr()
        assert captured.err != ''


# ---------------------------------------------------------------------------
# main: loop calls _run_once + sleep, Ctrl+C sends loop-stop and exits 0
# ---------------------------------------------------------------------------

class TestMainLoop:
    def test_loops_calling_run_once_and_sleep(self, tmp_path):
        from propeller.watch import main
        script = tmp_path / 'example.py'
        script.write_text('')

        with mock.patch('propeller.watch._run_once') as mock_run_once:
            with mock.patch('propeller.watch.time') as mock_time:
                mock_time.sleep.side_effect = [None, KeyboardInterrupt()]
                with mock.patch('propeller.watch.PropellerClient'):
                    with mock.patch('sys.argv', ['py-propeller', str(script)]):
                        with pytest.raises(SystemExit):
                            main()

        assert mock_run_once.call_count == 2
        mock_run_once.assert_called_with(str(script), 'active')

    def test_forwards_state_flag_to_run_once(self, tmp_path):
        from propeller.watch import main
        script = tmp_path / 'example.py'
        script.write_text('')

        with mock.patch('propeller.watch._run_once') as mock_run_once:
            with mock.patch('propeller.watch.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with mock.patch('propeller.watch.PropellerClient'):
                    with mock.patch('sys.argv', ['py-propeller', str(script), '-s', 'sync']):
                        with pytest.raises(SystemExit):
                            main()

        mock_run_once.assert_called_with(str(script), 'sync')

    def test_sleeps_for_configured_interval(self, tmp_path):
        from propeller.watch import main
        script = tmp_path / 'example.py'
        script.write_text('')

        with mock.patch('propeller.watch._run_once'):
            with mock.patch('propeller.watch.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with mock.patch('propeller.watch.PropellerClient'):
                    with mock.patch('sys.argv', ['py-propeller', str(script), '-n', '250']):
                        with pytest.raises(SystemExit):
                            main()

        mock_time.sleep.assert_called_with(0.25)

    def test_keyboard_interrupt_sends_loop_stop(self, tmp_path):
        from propeller.watch import main
        script = tmp_path / 'example.py'
        script.write_text('')

        with mock.patch('propeller.watch._run_once'):
            with mock.patch('propeller.watch.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with mock.patch('propeller.watch.PropellerClient') as mock_client_cls:
                    mock_instance = mock.MagicMock()
                    mock_client_cls.return_value = mock_instance
                    with mock.patch('sys.argv', ['py-propeller', str(script)]):
                        with pytest.raises(SystemExit) as exc_info:
                            main()

        assert exc_info.value.code == 0
        payload = json.loads(mock_instance.send.call_args[0][0])
        assert payload == {'command': 'loop-stop'}

    def test_loop_stop_failure_suppressed(self, tmp_path):
        from propeller.watch import main
        from propeller.errors import PropellerConnectionError
        script = tmp_path / 'example.py'
        script.write_text('')

        with mock.patch('propeller.watch._run_once'):
            with mock.patch('propeller.watch.time') as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt()
                with mock.patch('propeller.watch.PropellerClient') as mock_client_cls:
                    mock_instance = mock.MagicMock()
                    mock_instance.send.side_effect = PropellerConnectionError('gone')
                    mock_client_cls.return_value = mock_instance
                    with mock.patch('sys.argv', ['py-propeller', str(script)]):
                        with pytest.raises(SystemExit) as exc_info:
                            main()

        assert exc_info.value.code == 0
