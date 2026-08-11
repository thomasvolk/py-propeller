import json
import os
import socket
from typing import Protocol, runtime_checkable

from propeller.errors import PropellerConnectionError, PropellerResponseError

DEFAULT_SOCKET_PATH: str = os.environ.get('PROPELLER_SOCK', '/tmp/propeller.sock')


@runtime_checkable
class TransportProtocol(Protocol):
    def send(self, payload: str) -> None: ...
    def query(self, payload: str) -> dict: ...
    def __enter__(self) -> 'TransportProtocol': ...
    def __exit__(self, *args) -> None: ...


class PropellerClient:
    def send(self, payload: str) -> None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            try:
                sock.connect(DEFAULT_SOCKET_PATH)
            except OSError as e:
                raise PropellerConnectionError(
                    f"Cannot connect to {DEFAULT_SOCKET_PATH}: {e}. "
                    "Make sure the propeller-engine is running."
                ) from e
            sock.sendall((payload + '\n').encode('utf-8'))
            chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            response = json.loads(b''.join(chunks))
        if response['status'] == 'error':
            raise PropellerResponseError(code=response['code'], message=response.get('message'))
        return None

    def query(self, payload: str) -> dict:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            try:
                sock.connect(DEFAULT_SOCKET_PATH)
            except OSError as e:
                raise PropellerConnectionError(
                    f"Cannot connect to {DEFAULT_SOCKET_PATH}: {e}. "
                    "Make sure the propeller-engine is running."
                ) from e
            sock.sendall((payload + '\n').encode('utf-8'))
            chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            response = json.loads(b''.join(chunks))
        if response['status'] == 'error':
            raise PropellerResponseError(code=response['code'], message=response.get('message'))
        return response

    def __enter__(self) -> 'PropellerClient':
        return self

    def __exit__(self, *args) -> None:
        pass
