"""Deadline-aware output boundary; concrete audio and haptic drivers are injected."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from server.arbitration.core import OutputDecision


class OutputTransport(Protocol):
    def speak(self, text: str, deadline_ns: int) -> None: ...

    def cue(self, cue: str, deadline_ns: int) -> None: ...


@dataclass(frozen=True)
class ExecutionReceipt:
    decision_id: str
    status: Literal["applied", "rejected", "failed"]
    reason: str
    completed_ns: int


class SafeOutputExecutor:
    def __init__(self, transport: OutputTransport):
        self._transport = transport
        self._last_decision_id: str | None = None

    def execute(
        self, decision: OutputDecision, *, session_id: int, now_ns: int
    ) -> ExecutionReceipt:
        if not isinstance(decision, OutputDecision):
            raise TypeError("an arbitration decision is required")
        candidate = decision.candidate
        if not candidate.stamp.active(now_ns, session_id):
            return ExecutionReceipt(
                decision.decision_id, "rejected", "expired_or_wrong_session", now_ns
            )
        if decision.decision_id == self._last_decision_id:
            return ExecutionReceipt(decision.decision_id, "rejected", "duplicate_decision", now_ns)
        self._last_decision_id = decision.decision_id
        try:
            self._transport.speak(candidate.message, candidate.stamp.expires_ns)
            if candidate.cue != "none":
                self._transport.cue(candidate.cue, candidate.stamp.expires_ns)
        except Exception:
            return ExecutionReceipt(decision.decision_id, "failed", "transport_failure", now_ns)
        return ExecutionReceipt(decision.decision_id, "applied", "completed", now_ns)
