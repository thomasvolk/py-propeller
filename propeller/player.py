import json
import sys
import time

from propeller.serializer import serialize
from propeller.transport import PropellerClient


def _parse_state() -> str | None:
    if '-s' in sys.argv:
        idx = sys.argv.index('-s')
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return None


def play(project) -> None:
    if '-n' in sys.argv:
        payload = serialize(project)
        print(json.dumps(payload))
        return

    state = _parse_state()

    if state == 'inactive':
        PropellerClient().send(json.dumps({'command': 'loop-stop'}))
        sys.exit(0)

    if state == 'sync':
        payload = serialize(project)
        PropellerClient().send(json.dumps({'command': 'create-project', **payload}))
        sys.exit(0)

    if state == 'active':
        payload = serialize(project)
        response = PropellerClient().query(json.dumps({'command': 'status'}))
        if response.get('project_present'):
            cmd = json.dumps({'command': 'modify-project', **payload})
        else:
            cmd = json.dumps({'command': 'create-project', **payload})
        PropellerClient().send(cmd)
        PropellerClient().send(json.dumps({'command': 'loop-start'}))
        sys.exit(0)

    payload = serialize(project)
    create_cmd = json.dumps({'command': 'create-project', **payload})
    PropellerClient().send(create_cmd)

    PropellerClient().send(json.dumps({'command': 'loop-start'}))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        try:
            PropellerClient().send(json.dumps({'command': 'loop-stop'}))
        except Exception:
            pass
        sys.exit(0)
