"""Tests for the propeller.loop module (get-position)."""
from unittest import mock

import pytest


def _make_socket_mock(recv_responses):
    """Build a mock socket context manager with given recv side_effect."""
    mock_conn = mock.MagicMock()
    mock_conn.recv.side_effect = recv_responses
    mock_sock = mock.MagicMock()
    mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
    mock_sock.__exit__ = mock.Mock(return_value=False)
    return mock_sock, mock_conn


class TestGetPositionCommand:
    def test_sends_get_position_command(self):
        from propeller.loop import get_position
        mock_sock, mock_conn = _make_socket_mock(
            [b'{"tick":0,"loop_duration":1920,"loop_count":0}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            get_position()

        mock_conn.sendall.assert_called_once_with(
            b'{"command": "get-position"}\n'
        )


class TestGetPositionResponse:
    def test_returns_position_with_fields(self):
        from propeller.loop import get_position
        mock_sock, _ = _make_socket_mock(
            [b'{"tick":960,"loop_duration":1920,"loop_count":3}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            position = get_position()

        assert position.tick == 960
        assert position.loop_duration == 1920
        assert position.loop_count == 3

    def test_loop_duration_none_when_no_project(self):
        from propeller.loop import get_position
        mock_sock, _ = _make_socket_mock(
            [b'{"tick":0,"loop_duration":null,"loop_count":0}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            position = get_position()

        assert position.loop_duration is None


class TestGetPositionErrors:
    def test_raises_connection_error_on_failure(self):
        from propeller.errors import PropellerConnectionError
        from propeller.loop import get_position
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("Connection refused")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError):
                get_position()

    def test_raises_response_error_on_engine_error(self):
        from propeller.errors import PropellerResponseError
        from propeller.loop import get_position
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "unknown_command"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerResponseError) as exc_info:
                get_position()

        assert exc_info.value.code == 'unknown_command'
