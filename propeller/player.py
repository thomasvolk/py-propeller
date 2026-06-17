import json
import sys
import time

from propeller.serializer import serialize
from propeller.transport import PropellerClient


def play(project) -> None:
    if '-n' in sys.argv:
        payload = serialize(project)
        print(json.dumps({'command': 'create-project', **payload}))
        print(json.dumps({'command': 'loop-start'}))
        return

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
