import argparse
import json
import os
import runpy
import sys
import time
import traceback

from propeller.transport import PropellerClient


def _positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f'must be a positive integer: {value}')
    return ivalue


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='py-propeller',
        description=(
            'Re-evaluate a propeller composition script on an interval, '
            'pushing every change to a running propeller-engine.'
        ),
    )
    parser.add_argument('script', help='Path to the composition script to watch.')
    parser.add_argument(
        '-n', dest='interval_ms', type=_positive_int, default=100, metavar='MS',
        help='Re-evaluation interval in milliseconds (default: 100).',
    )
    parser.add_argument(
        '-s', dest='state', choices=['active', 'sync', 'inactive'], default='active',
        help=(
            "State to push on every re-evaluation (default: active). "
            "'sync' pushes project data only, leaving transport control to an "
            "external clock source."
        ),
    )
    args = parser.parse_args(argv)
    if not os.path.isfile(args.script):
        parser.error(f'no such file: {args.script}')
    return args


def _run_once(script: str, state: str = 'active') -> None:
    argv = sys.argv
    sys.argv = [script, '-s', state]
    try:
        runpy.run_path(script, run_name='__main__')
    except SystemExit as exc:
        if exc.code not in (0, None):
            traceback.print_exc()
    except Exception:
        traceback.print_exc()
    finally:
        sys.argv = argv


def main() -> None:
    args = _parse_args(sys.argv[1:])

    try:
        while True:
            _run_once(args.script, args.state)
            time.sleep(args.interval_ms / 1000)
    except KeyboardInterrupt:
        try:
            PropellerClient().send(json.dumps({'command': 'loop-stop'}))
        except Exception:
            pass
        sys.exit(0)


if __name__ == '__main__':
    main()
