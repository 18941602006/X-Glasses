"""Run a loopback dashboard; real PC jobs require an explicit startup flag."""

import argparse
from pathlib import Path

from server.api.http import create_server
from server.api.pc_jobs import PcJobs
from server.api.state import CommandBroker, DashboardStore
from server.api.warm_worker import WarmProcessRunner


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pc-runtime", action="store_true")
    parser.add_argument("--pc-python", type=Path, default=Path(".venv-pc/Scripts/python.exe"))
    args = parser.parse_args()
    store = DashboardStore()
    broker = CommandBroker(store)
    jobs = PcJobs(WarmProcessRunner(args.pc_python)) if args.pc_runtime else None
    server = create_server(store, broker, pc_jobs=jobs)
    print("X-Glasses local API: http://127.0.0.1:8765 (device dispatcher not attached)")
    print(
        f"PC evaluation jobs: {'enabled; explicit image/text requests only' if jobs else 'disabled'}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
