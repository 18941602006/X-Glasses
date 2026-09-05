"""Loopback-only dashboard API; never a hardware driver."""

from server.api.state import CommandBroker, DashboardStore, initial_snapshot

__all__ = ["CommandBroker", "DashboardStore", "initial_snapshot"]
