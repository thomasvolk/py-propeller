"""Integration tests for Epic 6: Validation & Error Feedback."""
from unittest import mock

import pytest

from propeller.errors import PropellerConnectionError, PropellerValidationError


class TestNoSocketOnValidationFailure:
    """T-8: Validation error before .play() must never open a socket."""

    def test_invalid_track_raises_before_socket(self):
        from propeller import project, track
        with mock.patch('socket.socket') as mock_socket_cls:
            with pytest.raises(PropellerValidationError):
                project(
                    bpm=120,
                    bars=2,
                    time_signature=(4, 4),
                    tracks=[track(name="X", channel=17, instrument=0, notes=[])],
                )
        mock_socket_cls.assert_not_called()

    def test_invalid_project_bpm_raises_before_socket(self):
        from propeller import project
        with mock.patch('socket.socket') as mock_socket_cls:
            with pytest.raises(PropellerValidationError):
                project(bpm=0, bars=2, time_signature=(4, 4), tracks=[])
        mock_socket_cls.assert_not_called()


class TestPlayConnectionError:
    """T-9: .play() on a valid project raises PropellerConnectionError when engine unreachable."""

    def test_play_raises_connection_error_when_unreachable(self):
        from propeller import project, track
        p = project(bpm=120, bars=2, time_signature=(4, 4), tracks=[])
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("Connection refused")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)
        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError) as exc_info:
                p.play()
        import propeller.transport as transport
        assert transport.DEFAULT_SOCKET_PATH in str(exc_info.value)

    def test_play_connection_error_contains_engine_suggestion(self):
        from propeller import project
        p = project(bpm=120, bars=2, time_signature=(4, 4), tracks=[])
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("Connection refused")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)
        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError) as exc_info:
                p.play()
        msg = str(exc_info.value).lower()
        assert 'running' in msg or 'engine' in msg

    def test_play_connection_error_cause_is_os_error(self):
        from propeller import project
        p = project(bpm=120, bars=2, time_signature=(4, 4), tracks=[])
        original = OSError("Connection refused")
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = original
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)
        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError) as exc_info:
                p.play()
        assert exc_info.value.__cause__ is original
