"""Handshake, liveness and ACK state machine; no automatic retry or actuator output."""

from collections import deque
from dataclasses import replace

from server.common.clock import ClockMapper
from server.common.control import (
    ACK,
    CLOCK_REQUEST,
    CLOCK_RESPONSE,
    HEARTBEAT,
    HELLO,
    WELCOME,
    AckResult,
    CommandResult,
    Opcode,
    command_payload,
)
from server.common.protocol import Kind, Packet
from server.common.sensors import decode_button, decode_imu, decode_tof
from server.input.frames import FRAME_TTL_NS
from server.input.stream import InputSession

HANDSHAKE_NS = 2_000_000_000
HEARTBEAT_NS = 1_500_000_000
COMMAND_TTL_NS = 500_000_000
MAX_PENDING = 8
MAX_TIME_ERROR_NS = 50_000_000


class HostLink:
    def __init__(self, origin: str):
        self.input = InputSession(origin)
        self.clock = ClockMapper()
        self.state = "disconnected"
        self.reason = "not_connected"
        self.nonce = 0
        self.boot_id = None
        self.capabilities = 0
        self.sequence = 0
        self.request_id = 0
        self.handshake_deadline = 0
        self.last_heartbeat = 0
        self.pending = {}
        self.clock_request = None
        self.results = deque(maxlen=32)
        self.buttons = deque(maxlen=32)
        self.sensors = {}
        self.malformed = 0
        self.orphan_acks = 0

    def _packet(self, kind, payload):
        packet = Packet(kind, self.input.session_id, self.sequence, 0, payload)
        self.sequence = (self.sequence + 1) & 0xFFFFFFFF
        return packet

    def _request_id(self):
        self.request_id += 1
        if self.request_id >= 2**64:
            raise RuntimeError("request id exhausted; establish a new session")
        return self.request_id

    def begin(self, session_id, nonce, now_ns):
        if not 0 < nonce < 2**64 or not 0 < session_id < 2**64:
            raise ValueError("fresh nonzero session and nonce required")
        self.disconnect(now_ns, "new_handshake")
        self.input.start(session_id, now_ns)
        self.nonce = nonce
        self.sequence = self.request_id = 0
        self.state = "handshaking"
        self.handshake_deadline = now_ns + HANDSHAKE_NS
        return self._packet(Kind.STATUS, HELLO.pack(1, nonce))

    def disconnect(self, now_ns, reason="disconnected"):
        old_session = self.input.session_id
        self.input.disconnect(now_ns)
        for request_id, (opcode, _) in self.pending.items():
            self.results.append(CommandResult(request_id, opcode, "disconnected", old_session))
        self.pending.clear()
        self.buttons.clear()
        self.sensors.clear()
        self.clock.reset()
        self.clock_request = None
        self.boot_id = None
        self.capabilities = 0
        self.state, self.reason = "disconnected", reason

    def tick(self, now_ns):
        if self.state == "handshaking" and now_ns >= self.handshake_deadline:
            self.disconnect(now_ns, "handshake_timeout")
        elif self.state == "ready" and now_ns - self.last_heartbeat >= HEARTBEAT_NS:
            self.disconnect(now_ns, "heartbeat_timeout")
        for request_id, (opcode, deadline) in list(self.pending.items()):
            if now_ns >= deadline:
                self.results.append(
                    CommandResult(request_id, opcode, "timeout", self.input.session_id)
                )
                del self.pending[request_id]
        if self.clock_request is not None and now_ns - self.clock_request[1] >= HANDSHAKE_NS:
            self.clock_request = None
        self._process(self.input.feed(b"", now_ns), now_ns)

    def feed(self, data, now_ns):
        self.tick(now_ns)
        self._process(self.input.feed(data, now_ns), now_ns)

    def _process(self, packets, now_ns):
        for packet in packets:
            try:
                if self.state == "handshaking":
                    self.input.frames.reset()  # No pre-handshake image can later become live.
                    if packet.kind != Kind.STATUS or len(packet.payload) != WELCOME.size:
                        continue
                    subtype, nonce, boot_id, capabilities = WELCOME.unpack(packet.payload)
                    if subtype != 2 or nonce != self.nonce or boot_id == 0:
                        continue
                    self.boot_id, self.capabilities = boot_id, capabilities
                    self.state, self.reason = "ready", "connected_unsynchronized"
                    self.last_heartbeat = now_ns
                elif self.state == "ready":
                    self._handle(packet, now_ns)
            except ValueError:
                self.malformed += 1
                self.sensors.pop(packet.kind, None)

    def _handle(self, packet, now_ns):
        if packet.kind == Kind.STATUS:
            if len(packet.payload) != HEARTBEAT.size:
                raise ValueError("invalid heartbeat")
            subtype, boot = HEARTBEAT.unpack(packet.payload)
            if subtype != 3:
                raise ValueError("invalid heartbeat subtype")
            if boot != self.boot_id:
                self.disconnect(now_ns, "device_reboot")
            else:
                self.last_heartbeat = now_ns
        elif packet.kind == Kind.CLOCK:
            if len(packet.payload) != CLOCK_RESPONSE.size:
                raise ValueError("invalid clock response")
            request, sent, received_us, sent_us = CLOCK_RESPONSE.unpack(packet.payload)
            if self.clock_request != (request, sent):
                raise ValueError("unsolicited clock response")
            self.clock_request = None
            self.clock.observe(sent, received_us, sent_us, now_ns)
            self.reason = "connected_clock_estimated"
        elif packet.kind == Kind.ACK:
            if len(packet.payload) != ACK.size:
                raise ValueError("invalid ACK")
            request, opcode, result = ACK.unpack(packet.payload)
            result = AckResult(result)
            pending = self.pending.get(request)
            if pending is None or pending[0] != opcode:
                self.orphan_acks += 1
                return
            del self.pending[request]
            self.results.append(
                CommandResult(request, Opcode(opcode), result.name.lower(), packet.session_id)
            )
        elif packet.kind in (Kind.TOF, Kind.IMU):
            decoder = decode_tof if packet.kind == Kind.TOF else decode_imu
            self.sensors[packet.kind] = (decoder(packet.payload), packet.capture_us, now_ns)
        elif packet.kind == Kind.BUTTON:
            self.buttons.append((decode_button(packet.payload), packet.capture_us, now_ns))

    def request_clock(self, now_ns):
        self.tick(now_ns)
        if self.state != "ready" or self.clock_request is not None:
            raise RuntimeError("ready link with no outstanding clock request required")
        request = self._request_id()
        self.clock_request = (request, now_ns)
        return self._packet(Kind.CLOCK, CLOCK_REQUEST.pack(request, now_ns))

    def command(self, opcode, now_ns, duration_ms=0, intensity=0):
        self.tick(now_ns)
        if self.state != "ready" or len(self.pending) >= MAX_PENDING:
            raise RuntimeError("link unavailable or command queue full")
        opcode = Opcode(opcode)
        deadline_us = 0
        if opcode not in (Opcode.STOP_STREAM, Opcode.CANCEL_HAPTIC):
            deadline_us = self.clock.device_deadline(now_ns, COMMAND_TTL_NS)
        request = self._request_id()
        payload = command_payload(request, opcode, deadline_us, duration_ms, intensity)
        self.pending[request] = (opcode, now_ns + COMMAND_TTL_NS)
        return self._packet(Kind.COMMAND, payload)

    def _fresh_time(self, capture_us, received_ns, now_ns):
        estimate = self.clock.map(capture_us, now_ns)
        if estimate is None or estimate.uncertainty_ns > MAX_TIME_ERROR_NS:
            return None
        if not 0 <= now_ns - received_ns < FRAME_TTL_NS:
            return None
        # Worst-case age and future timestamp bound, not just estimated midpoint age.
        if now_ns - estimate.host_ns + estimate.uncertainty_ns >= FRAME_TTL_NS:
            return None
        if estimate.host_ns - now_ns > estimate.uncertainty_ns:
            return None
        return estimate

    def take_frame(self, now_ns):
        self.tick(now_ns)
        frame = self.input.pop_latest(now_ns)
        if frame is None or self.state != "ready":
            return None
        estimate = self._fresh_time(frame.capture_us, frame.first_received_ns, now_ns)
        if estimate is None:
            return None
        return replace(
            frame,
            mapped_capture_ns=estimate.host_ns,
            timing_status="estimated",
            time_uncertainty_ns=estimate.uncertainty_ns,
        )

    def take_buttons(self, now_ns):
        self.tick(now_ns)
        events = []
        while self.buttons:
            event, capture_us, received_ns = self.buttons.popleft()
            if self.state == "ready" and self._fresh_time(capture_us, received_ns, now_ns):
                events.append(event)
        return events

    def sensor(self, kind, now_ns):
        self.tick(now_ns)
        entry = self.sensors.get(kind)
        if entry is None or self.state != "ready":
            return None
        value, capture_us, received_ns = entry
        estimate = self._fresh_time(capture_us, received_ns, now_ns)
        if estimate is None:
            return None
        return value, estimate
