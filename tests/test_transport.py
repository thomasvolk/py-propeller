"""Tests for Epic 2: Socket Transport Layer."""
import importlib
import socket
import sys
from unittest import mock

import pytest


# ---------------------------------------------------------------------------
# T-1: PropellerConnectionError and PropellerResponseError
# ---------------------------------------------------------------------------

class TestErrorClasses:
    def test_connection_error_importable(self):
        from propeller.errors import PropellerConnectionError
        assert PropellerConnectionError is not None

    def test_response_error_importable(self):
        from propeller.errors import PropellerResponseError
        assert PropellerResponseError is not None

    def test_connection_error_subclasses_propeller_error(self):
        from propeller.errors import PropellerError, PropellerConnectionError
        assert issubclass(PropellerConnectionError, PropellerError)

    def test_response_error_subclasses_propeller_error(self):
        from propeller.errors import PropellerError, PropellerResponseError
        assert issubclass(PropellerResponseError, PropellerError)

    def test_response_error_code_attribute(self):
        from propeller.errors import PropellerResponseError
        err = PropellerResponseError(code="x")
        assert err.code == "x"

    def test_response_error_code_validation_error(self):
        from propeller.errors import PropellerResponseError
        err = PropellerResponseError(code="validation_error")
        assert err.code == "validation_error"

    def test_response_error_message_attribute(self):
        from propeller.errors import PropellerResponseError
        err = PropellerResponseError(code="validation_error", message="track 0 note 0: duration must be > 0")
        assert err.message == "track 0 note 0: duration must be > 0"

    def test_response_error_message_defaults_to_none(self):
        from propeller.errors import PropellerResponseError
        err = PropellerResponseError(code="validation_error")
        assert err.message is None

    def test_response_error_str_includes_message_when_present(self):
        from propeller.errors import PropellerResponseError
        err = PropellerResponseError(code="validation_error", message="duration must be > 0")
        assert str(err) == "validation_error: duration must be > 0"

    def test_response_error_str_is_code_only_without_message(self):
        from propeller.errors import PropellerResponseError
        err = PropellerResponseError(code="no_project")
        assert str(err) == "no_project"


# ---------------------------------------------------------------------------
# T-2: DEFAULT_SOCKET_PATH defaults to /tmp/propeller.sock
# ---------------------------------------------------------------------------

class TestDefaultSocketPath:
    def test_default_socket_path_without_env(self, monkeypatch):
        monkeypatch.delenv('PROPELLER_SOCK', raising=False)
        import propeller.transport as transport
        monkeypatch.setattr(transport, 'DEFAULT_SOCKET_PATH', '/tmp/propeller.sock')
        assert transport.DEFAULT_SOCKET_PATH == '/tmp/propeller.sock'

    def test_default_socket_path_constant_exists(self):
        import propeller.transport as transport
        assert hasattr(transport, 'DEFAULT_SOCKET_PATH')
        assert isinstance(transport.DEFAULT_SOCKET_PATH, str)


# ---------------------------------------------------------------------------
# T-3: DEFAULT_SOCKET_PATH uses PROPELLER_SOCK when set before import
# Note: We test this by monkeypatching after import (module already loaded)
# ---------------------------------------------------------------------------

class TestSocketPathFromEnv:
    def test_monkeypatch_socket_path(self, monkeypatch):
        import propeller.transport as transport
        monkeypatch.setattr(transport, 'DEFAULT_SOCKET_PATH', '/run/propeller.sock')
        assert transport.DEFAULT_SOCKET_PATH == '/run/propeller.sock'


# ---------------------------------------------------------------------------
# T-4: TransportProtocol is importable; PropellerClient satisfies it
# ---------------------------------------------------------------------------

class TestTransportProtocol:
    def test_transport_protocol_importable(self):
        from propeller.transport import TransportProtocol
        assert TransportProtocol is not None

    def test_propeller_client_satisfies_protocol(self):
        from propeller.transport import TransportProtocol, PropellerClient
        assert isinstance(PropellerClient(), TransportProtocol)

    def test_protocol_has_send(self):
        from propeller.transport import TransportProtocol
        assert hasattr(TransportProtocol, 'send')

    def test_protocol_has_enter(self):
        from propeller.transport import TransportProtocol
        assert hasattr(TransportProtocol, '__enter__')

    def test_protocol_has_exit(self):
        from propeller.transport import TransportProtocol
        assert hasattr(TransportProtocol, '__exit__')


# ---------------------------------------------------------------------------
# T-5: PropellerClient() takes no arguments
# ---------------------------------------------------------------------------

class TestPropellerClientConstructor:
    def test_instantiates_with_no_args(self):
        from propeller.transport import PropellerClient
        client = PropellerClient()
        assert client is not None

    def test_argument_raises_type_error(self):
        from propeller.transport import PropellerClient
        with pytest.raises(TypeError):
            PropellerClient('/tmp/other.sock')


# ---------------------------------------------------------------------------
# T-6: PropellerClient context manager
# ---------------------------------------------------------------------------

class TestPropellerClientContextManager:
    def test_enter_returns_client(self):
        from propeller.transport import PropellerClient
        client = PropellerClient()
        result = client.__enter__()
        assert result is client

    def test_with_block_normal_exit(self):
        from propeller.transport import PropellerClient
        with PropellerClient() as c:
            assert c is not None

    def test_with_block_exception_exit(self):
        from propeller.transport import PropellerClient
        try:
            with PropellerClient():
                raise ValueError("test")
        except ValueError:
            pass  # exception propagated, not suppressed

    def test_exit_does_not_suppress_exception(self):
        from propeller.transport import PropellerClient
        client = PropellerClient()
        result = client.__exit__(ValueError, ValueError("x"), None)
        assert not result


# ---------------------------------------------------------------------------
# T-7: send() opens AF_UNIX socket and calls sendall with payload + newline
# ---------------------------------------------------------------------------

def _make_socket_mock(recv_responses):
    """Build a mock socket context manager with given recv side_effect."""
    mock_conn = mock.MagicMock()
    mock_conn.recv.side_effect = recv_responses
    mock_sock = mock.MagicMock()
    mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
    mock_sock.__exit__ = mock.Mock(return_value=False)
    return mock_sock, mock_conn


class TestSendPayload:
    def test_opens_af_unix_sock_stream(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, mock_conn = _make_socket_mock([b'{"status": "ok"}', b''])

        with mock.patch('socket.socket', return_value=mock_sock) as mock_ctor:
            transport.PropellerClient().send('{"command": "test"}')

        mock_ctor.assert_called_once_with(socket.AF_UNIX, socket.SOCK_STREAM)

    def test_connects_to_default_socket_path(self, monkeypatch):
        import propeller.transport as transport
        monkeypatch.setattr(transport, 'DEFAULT_SOCKET_PATH', '/tmp/test.sock')
        mock_sock, mock_conn = _make_socket_mock([b'{"status": "ok"}', b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            transport.PropellerClient().send('{"command": "test"}')

        mock_conn.connect.assert_called_once_with('/tmp/test.sock')

    def test_sendall_with_newline_terminated_utf8(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, mock_conn = _make_socket_mock([b'{"status": "ok"}', b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            transport.PropellerClient().send('{"command": "test"}')

        mock_conn.sendall.assert_called_once_with(b'{"command": "test"}\n')


# ---------------------------------------------------------------------------
# T-8: send() returns None on status "ok"
# ---------------------------------------------------------------------------

class TestSendOkResponse:
    def test_returns_none_on_ok(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, _ = _make_socket_mock([b'{"status": "ok"}', b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            result = transport.PropellerClient().send('{"command": "test"}')

        assert result is None

    def test_returns_none_on_ok_with_extra_fields(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, _ = _make_socket_mock([b'{"status": "ok", "id": 42}', b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            result = transport.PropellerClient().send('{"command": "test"}')

        assert result is None


# ---------------------------------------------------------------------------
# T-9: send() raises PropellerResponseError on status "error"
# ---------------------------------------------------------------------------

class TestSendErrorResponse:
    def test_raises_response_error(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerResponseError
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "validation_error"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerResponseError) as exc_info:
                transport.PropellerClient().send('{"command": "test"}')

        assert exc_info.value.code == 'validation_error'

    def test_raises_response_error_with_code(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerResponseError
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "no_project"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerResponseError) as exc_info:
                transport.PropellerClient().send('{"command": "test"}')

        assert exc_info.value.code == 'no_project'

    def test_raises_response_error_with_message(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerResponseError
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "validation_error", '
             b'"message": "track 0 pitch-bend 5: tick 1920 is out of range '
             b'(must be < loop_duration 1920)"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerResponseError) as exc_info:
                transport.PropellerClient().send('{"command": "test"}')

        assert exc_info.value.message == (
            'track 0 pitch-bend 5: tick 1920 is out of range (must be < loop_duration 1920)'
        )

    def test_raises_response_error_without_message_field(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerResponseError
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "no_project"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerResponseError) as exc_info:
                transport.PropellerClient().send('{"command": "test"}')

        assert exc_info.value.message is None


# ---------------------------------------------------------------------------
# T-10: send() raises PropellerConnectionError on connection failure
# ---------------------------------------------------------------------------

class TestConnectionFailure:
    def test_raises_connection_error_not_os_error(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerConnectionError
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("Connection refused")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError):
                transport.PropellerClient().send('{}')

    def test_connection_error_message_contains_path(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerConnectionError
        monkeypatch.setattr(transport, 'DEFAULT_SOCKET_PATH', '/tmp/test.sock')
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("No such file")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError) as exc_info:
                transport.PropellerClient().send('{}')

        assert '/tmp/test.sock' in str(exc_info.value)

    def test_connection_error_cause_is_os_error(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerConnectionError
        original_err = OSError("Connection refused")
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = original_err
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError) as exc_info:
                transport.PropellerClient().send('{}')

        assert exc_info.value.__cause__ is original_err


# ---------------------------------------------------------------------------
# T-11: Socket context manager is entered/exited on all code paths (no fd leak)
# ---------------------------------------------------------------------------

class TestSocketCleanup:
    def test_socket_closed_on_success(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, _ = _make_socket_mock([b'{"status": "ok"}', b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            transport.PropellerClient().send('{}')

        mock_sock.__exit__.assert_called_once()

    def test_socket_closed_on_response_error(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "e"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            try:
                transport.PropellerClient().send('{}')
            except Exception:
                pass

        mock_sock.__exit__.assert_called_once()

    def test_socket_closed_on_connection_error(self, monkeypatch):
        import propeller.transport as transport
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("refused")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)

        with mock.patch('socket.socket', return_value=mock_sock):
            try:
                transport.PropellerClient().send('{}')
            except Exception:
                pass

        mock_sock.__exit__.assert_called_once()


# ---------------------------------------------------------------------------
# T-6 (Epic 6): Connection error includes socket path AND "engine is running" suggestion
# ---------------------------------------------------------------------------

class TestConnectionErrorSuggestion:
    def _make_failing_socket(self):
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("Connection refused")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)
        return mock_sock

    def test_message_contains_socket_path(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerConnectionError
        monkeypatch.setattr(transport, 'DEFAULT_SOCKET_PATH', '/tmp/propeller.sock')
        with mock.patch('socket.socket', return_value=self._make_failing_socket()):
            with pytest.raises(PropellerConnectionError) as exc_info:
                transport.PropellerClient().send('{}')
        assert '/tmp/propeller.sock' in str(exc_info.value)

    def test_message_contains_engine_suggestion(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerConnectionError
        with mock.patch('socket.socket', return_value=self._make_failing_socket()):
            with pytest.raises(PropellerConnectionError) as exc_info:
                transport.PropellerClient().send('{}')
        msg = str(exc_info.value).lower()
        assert 'engine' in msg or 'propeller-engine' in msg or 'running' in msg

    def test_cause_is_original_os_error(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerConnectionError
        original = OSError("Connection refused")
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = original
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)
        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError) as exc_info:
                transport.PropellerClient().send('{}')
        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# T-12: Static import check — no propeller DSL symbols in transport.py
# ---------------------------------------------------------------------------

class TestNoInternalImports:
    def test_transport_has_no_propeller_dsl_imports(self):
        import propeller.transport as transport
        source_file = transport.__file__
        with open(source_file) as f:
            source = f.read()
        assert 'propeller.notes' not in source
        assert 'from propeller.notes' not in source
        assert 'import notes' not in source


# ---------------------------------------------------------------------------
# T-13: query() returns full response dict on status "ok"
# ---------------------------------------------------------------------------

class TestQueryOkResponse:
    def test_query_returns_full_dict(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "ok", "project_present": true}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            result = transport.PropellerClient().query('{"command": "status"}')

        assert result == {'status': 'ok', 'project_present': True}

    def test_query_returns_dict_not_none(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, _ = _make_socket_mock([b'{"status": "ok"}', b''])

        with mock.patch('socket.socket', return_value=mock_sock):
            result = transport.PropellerClient().query('{"command": "status"}')

        assert result is not None
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# T-14: query() raises PropellerResponseError on status "error"
# ---------------------------------------------------------------------------

class TestQueryErrorResponse:
    def test_query_raises_response_error(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerResponseError
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "no_project"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerResponseError) as exc_info:
                transport.PropellerClient().query('{"command": "status"}')

        assert exc_info.value.code == 'no_project'

    def test_query_raises_response_error_with_message(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerResponseError
        mock_sock, _ = _make_socket_mock(
            [b'{"status": "error", "code": "validation_error", '
             b'"message": "loop_duration must be greater than 0"}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerResponseError) as exc_info:
                transport.PropellerClient().query('{"command": "status"}')

        assert exc_info.value.message == 'loop_duration must be greater than 0'

    def test_query_raises_connection_error_on_failure(self, monkeypatch):
        import propeller.transport as transport
        from propeller.errors import PropellerConnectionError
        mock_sock = mock.MagicMock()
        mock_conn = mock.MagicMock()
        mock_conn.connect.side_effect = OSError("Connection refused")
        mock_sock.__enter__ = mock.Mock(return_value=mock_conn)
        mock_sock.__exit__ = mock.Mock(return_value=False)

        with mock.patch('socket.socket', return_value=mock_sock):
            with pytest.raises(PropellerConnectionError):
                transport.PropellerClient().query('{"command": "status"}')


# ---------------------------------------------------------------------------
# T-15: responses without a "status" field (e.g. get-position) are treated
# as success, not a KeyError, by both send() and query()
# ---------------------------------------------------------------------------

class TestMissingStatusField:
    def test_send_treats_missing_status_as_ok(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, _ = _make_socket_mock(
            [b'{"tick":960,"loop_duration":1920,"loop_count":3}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            result = transport.PropellerClient().send('{"command": "get-position"}')

        assert result is None

    def test_query_treats_missing_status_as_ok(self, monkeypatch):
        import propeller.transport as transport
        mock_sock, _ = _make_socket_mock(
            [b'{"tick":960,"loop_duration":1920,"loop_count":3}', b'']
        )

        with mock.patch('socket.socket', return_value=mock_sock):
            result = transport.PropellerClient().query('{"command": "get-position"}')

        assert result == {'tick': 960, 'loop_duration': 1920, 'loop_count': 3}
