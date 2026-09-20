import json
import sys
import time

from propeller import engine
from propeller.serializer import serialize


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
        engine.loop_stop()
        sys.exit(0)

    if state == 'sync':
        payload = serialize(project)
        engine.create_project(payload)
        sys.exit(0)

    if state == 'active':
        payload = serialize(project)
        response = engine.status()
        if response.project_present:
            engine.modify_project(payload)
        else:
            engine.create_project(payload)
        engine.loop_start()
        sys.exit(0)

    payload = serialize(project)
    engine.create_project(payload)

    engine.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        try:
            engine.loop_stop()
        except Exception:
            pass
        sys.exit(0)
