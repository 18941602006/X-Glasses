"""Bounded worker adapter. A caller must explicitly provide an isolated transport."""

from __future__ import annotations

import base64
from typing import Protocol

from server.perception.assist.contracts import (
    DialogueEvent,
    EventStamp,
    OcrEvent,
    TrafficSignalEvent,
    bounded_text,
    parse_dialogue_response,
    parse_ocr_response,
    parse_signal_response,
)

MAX_JPEG = 256 * 1024
MAX_QUESTION = 1000


class AssistFailure(RuntimeError):
    pass


class AssistTransport(Protocol):
    def request(self, message: dict, timeout_ms: int) -> dict: ...


class AssistWorkerAdapter:
    def __init__(
        self,
        transport: AssistTransport,
        *,
        signal_model_id: str,
        ocr_model_id: str,
        dialogue_provider_id: str,
        dialogue_model_id: str,
        timeout_ms: int = 3000,
    ):
        for name, value in (
            ("signal model", signal_model_id),
            ("OCR model", ocr_model_id),
            ("dialogue provider", dialogue_provider_id),
            ("dialogue model", dialogue_model_id),
        ):
            bounded_text(value, name, 120)
        if not 100 <= timeout_ms <= 10_000:
            raise ValueError("bounded worker timeout required")
        self._transport = transport
        self.signal_model_id = signal_model_id
        self.ocr_model_id = ocr_model_id
        self.dialogue_provider_id = dialogue_provider_id
        self.dialogue_model_id = dialogue_model_id
        self.timeout_ms = timeout_ms

    @staticmethod
    def _jpeg(value: bytes) -> str:
        if (
            not isinstance(value, bytes)
            or not 4 <= len(value) <= MAX_JPEG
            or not value.startswith(b"\xff\xd8")
            or not value.endswith(b"\xff\xd9")
        ):
            raise ValueError("bounded JPEG required")
        return base64.b64encode(value).decode("ascii")

    def _request(self, message: dict) -> dict:
        try:
            response = self._transport.request(message, self.timeout_ms)
        except TimeoutError as exc:
            raise AssistFailure("assist worker timeout") from exc
        except Exception as exc:
            raise AssistFailure("assist worker unavailable") from exc
        if not isinstance(response, dict):
            raise AssistFailure("assist worker returned non-object")
        return response

    def recognize_signal(self, jpeg: bytes, stamp: EventStamp) -> TrafficSignalEvent:
        response = self._request(
            {
                "schema": "xg.signal.request.v1",
                "session_id": str(stamp.session_id),
                "correlation_id": stamp.correlation_id,
                "jpeg_base64": self._jpeg(jpeg),
            }
        )
        try:
            return parse_signal_response(response, stamp, self.signal_model_id)
        except (TypeError, ValueError) as exc:
            raise AssistFailure("invalid signal worker response") from exc

    def read_text(self, jpeg: bytes, stamp: EventStamp) -> OcrEvent:
        response = self._request(
            {
                "schema": "xg.ocr.request.v1",
                "session_id": str(stamp.session_id),
                "correlation_id": stamp.correlation_id,
                "jpeg_base64": self._jpeg(jpeg),
            }
        )
        try:
            return parse_ocr_response(response, stamp, self.ocr_model_id)
        except (TypeError, ValueError) as exc:
            raise AssistFailure("invalid OCR worker response") from exc

    def ask(self, question: str, stamp: EventStamp) -> DialogueEvent:
        bounded_text(question, "dialogue question", MAX_QUESTION)
        response = self._request(
            {
                "schema": "xg.dialogue.request.v1",
                "session_id": str(stamp.session_id),
                "correlation_id": stamp.correlation_id,
                "text": question,
            }
        )
        try:
            return parse_dialogue_response(
                response, stamp, self.dialogue_provider_id, self.dialogue_model_id
            )
        except (TypeError, ValueError) as exc:
            raise AssistFailure("invalid dialogue worker response") from exc
