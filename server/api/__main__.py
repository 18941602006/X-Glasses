"""Run an offline-safe dashboard API on 127.0.0.1:8765."""

from server.api.http import create_server
from server.api.state import CommandBroker, DashboardStore


def main() -> None:
    store = DashboardStore()
    broker = CommandBroker(store)
    server = create_server(store, broker)
    print("X-Glasses local API: http://127.0.0.1:8765 (device dispatcher not attached)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
