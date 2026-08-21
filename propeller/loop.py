import json
from dataclasses import dataclass

from propeller.transport import PropellerClient


@dataclass(frozen=True)
class Position:
    tick: int
    loop_duration: int | None
    loop_count: int


def get_position() -> Position:
    response = PropellerClient().query(json.dumps({'command': 'get-position'}))
    return Position(
        tick=response['tick'],
        loop_duration=response['loop_duration'],
        loop_count=response['loop_count'],
    )
