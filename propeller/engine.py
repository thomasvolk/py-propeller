import json
from dataclasses import dataclass

from propeller.transport import PropellerClient


@dataclass(frozen=True)
class Status:
    status: str
    mode: str
    bpm: int | None
    loop_duration: int | None
    clock_state: str
    project_present: bool
    midi_port_name: str | None
    sync_port_name: str | None
    sync_clock_state: str | None


@dataclass(frozen=True)
class Position:
    tick: int
    loop_duration: int | None
    loop_count: int


def status() -> Status:
    response = PropellerClient().query(json.dumps({'command': 'status'}))
    return Status(
        status=response['status'],
        mode=response['mode'],
        bpm=response.get('bpm'),
        loop_duration=response.get('loop_duration'),
        clock_state=response['clock_state'],
        project_present=response['project_present'],
        midi_port_name=response.get('midi_port_name'),
        sync_port_name=response.get('sync_port_name'),
        sync_clock_state=response.get('sync_clock_state'),
    )


def get_position() -> Position:
    response = PropellerClient().query(json.dumps({'command': 'get-position'}))
    return Position(
        tick=response['tick'],
        loop_duration=response['loop_duration'],
        loop_count=response['loop_count'],
    )


def loop_start() -> None:
    PropellerClient().send(json.dumps({'command': 'loop-start'}))


def loop_stop() -> None:
    PropellerClient().send(json.dumps({'command': 'loop-stop'}))


def create_project(payload: dict) -> None:
    PropellerClient().send(json.dumps({'command': 'create-project', **payload}))


def modify_project(payload: dict) -> None:
    PropellerClient().send(json.dumps({'command': 'modify-project', **payload}))


def clear_project() -> None:
    PropellerClient().send(json.dumps({'command': 'clear-project'}))
