"""Tests for the propeller.status module (status)."""
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


_FULL_RESPONSE = (
    b'{"status":"ok","mode":"standalone","bpm":120,"loop_duration":1920,'
    b'"clock_state":"started","project_present":true,'
    b'"midi_port_name":"IAC Driver Bus 1","sync_port_name":"Sync Out",'
    b'"sync_clock_state":"tracking"}'
)

_MINIMAL_RESPONSE = (
    b'{"status":"ok","mode":"standalone","bpm":120,'
    b'"clock_state":"stopped","project_present":false}'
)


class TestStatusCommand:
    def test_sends_status_command(self):
        from propeller.status import get_status
        mock_sock, mock_conn = _make_socket_mock([_FULL_RESPONSE, b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            get_status()

        mock_conn.sendall.assert_called_once_with(
            b'{"command": "status"}\n'
        )


class TestStatusResponse:
    def test_returns_status_with_fields(self):
        from propeller.status import get_status
        mock_sock, _ = _make_socket_mock([_FULL_RESPONSE, b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            status = get_status()

        assert status.status == 'ok'
        assert status.mode == 'standalone'
        assert status.bpm == 120
        assert status.loop_duration == 1920
        assert status.clock_state == 'started'
        assert status.project_present is True
        assert status.midi_port_name == 'IAC Driver Bus 1'
        assert status.sync_port_name == 'Sync Out'
        assert status.sync_clock_state == 'tracking'

    def test_absent_fields_are_none(self):
        from propeller.status import get_status
        mock_sock, _ = _make_socket_mock([_MINIMAL_RESPONSE, b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            status = get_status()

        assert status.loop_duration is None
        assert status.midi_port_name is None
        assert status.sync_port_name is None
        assert status.sync_clock_state is None


class TestStatusErrors:
    def test_raises_connection_error_on_failure(self):
        from propeller.errors import PropellerConnectionError
        from propeller.status import get_status
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("Connection refused")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError):
                get_status()

    def test_raises_response_error_on_engine_error(self):
        from propeller.errors import PropellerResponseError
        from propeller.status import get_status
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "unknown_command"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerResponseError) as exc_info:
                get_status()

        assert exc_info.value.code == 'unknown_command'
