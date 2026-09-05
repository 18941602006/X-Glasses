"""Wire definitions shared with future firmware; host ledger does not execute hardware."""

from dataclasses import dataclass
from enum import IntEnum
from struct import Struct

HELLO = Struct("<BQ")  # status subtype=1, host nonce
WELCOME = Struct("<BQQI")  # subtype=2, nonce, boot id, capability bitmap
HEARTBEAT = Struct("<BQ")  # subtype=3, boot id
CLOCK_REQUEST = Struct("<QQ")  # request id, original host send ns
CLOCK_RESPONSE = Struct("<QQQQ")  # request id, host send ns, device rx us, device tx us
COMMAND = Struct("<QBQHB")  # request id, opcode, device deadline us, duration ms, intensity
ACK = Struct("<QBB")  # request id, opcode, result

CAP_CLOCK = 1 << 0
CAP_TOF = 1 << 1
CAP_IMU = 1 << 2
CAP_BUTTON = 1 << 3
CAP_CAMERA = 1 << 4
CAP_HAPTIC = 1 << 5


class Opcode(IntEnum):
    START_STREAM = 1
    STOP_STREAM = 2
    HAPTIC = 3
    CANCEL_HAPTIC = 4


class AckResult(IntEnum):
    APPLIED = 1
    REJECTED = 2
    EXPIRED = 3


@dataclass(frozen=True)
class CommandResult:
    request_id: int
    opcode: Opcode
    state: str
    session_id: int


def command_payload(request_id, opcode, deadline_us, duration_ms=0, intensity=0):
    opcode = Opcode(opcode)
    if not 0 < request_id < 2**64 or not 0 <= deadline_us < 2**64:
        raise ValueError("invalid command identifier/deadline")
    if opcode == Opcode.HAPTIC:
        if not 1 <= duration_ms <= 500 or not 1 <= intensity <= 255 or deadline_us == 0:
            raise ValueError("bounded haptic duration/intensity/deadline required")
    elif duration_ms or intensity:
        raise ValueError("non-haptic command must not carry actuator parameters")
    if opcode == Opcode.START_STREAM and deadline_us == 0:
        raise ValueError("start requires a device deadline")
    return COMMAND.pack(request_id, opcode, deadline_us, duration_ms, intensity)
