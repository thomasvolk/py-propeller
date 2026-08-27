import json
from dataclasses import dataclass

from propeller.transport import PropellerClient


@dataclass(frozen=True)
class Status:
    status: str
    mode: str
    bpm: int
    loop_duration: int | None
    clock_state: str
    project_present: bool
    midi_port_name: str | None
    sync_port_name: str | None
    sync_clock_state: str


def get_status() -> Status:
    response = PropellerClient().query(json.dumps({'command': 'status'}))
    return Status(
        status=response['status'],
        mode=response['mode'],
        bpm=response['bpm'],
        loop_duration=response.get('loop_duration'),
        clock_state=response['clock_state'],
        project_present=response['project_present'],
        midi_port_name=response.get('midi_port_name'),
        sync_port_name=response.get('sync_port_name'),
        sync_clock_state=response['sync_clock_state'],
    )
