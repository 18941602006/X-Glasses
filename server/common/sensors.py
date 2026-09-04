"""Normalized sensor wire messages; raw invalid readings never become clear space."""

import math
from dataclasses import dataclass
from struct import Struct

TOF_HEADER = Struct("<IBB")
ZONE = Struct("<HBB")  # mm or 0xffff, normalized valid (0/1), original driver status
IMU = Struct("<I6fB")  # sample id, acceleration m/s^2, angular velocity rad/s, valid
BUTTON = Struct("<IBB")  # event id, physical button 1/2, release=0/press=1


@dataclass(frozen=True)
class TofZone:
    distance_mm: int | None
    raw_status: int


@dataclass(frozen=True)
class TofSample:
    sample_id: int
    rows: int
    columns: int
    zones: tuple[TofZone, ...]


def decode_tof(payload: bytes) -> TofSample:
    if len(payload) < TOF_HEADER.size:
        raise ValueError("short ToF header")
    sample, rows, columns = TOF_HEADER.unpack_from(payload)
    if (rows, columns) not in ((4, 4), (8, 8)):
        raise ValueError("unsupported ToF resolution")
    if len(payload) != TOF_HEADER.size + rows * columns * ZONE.size:
        raise ValueError("ToF zone count mismatch")
    zones = []
    for offset in range(TOF_HEADER.size, len(payload), ZONE.size):
        distance, valid, raw_status = ZONE.unpack_from(payload, offset)
        if valid not in (0, 1):
            raise ValueError("unknown ToF validity code")
        if valid and not 0 < distance < 65535:
            raise ValueError("invalid valid-zone distance")
        if not valid and distance != 65535:
            raise ValueError("unknown zone must use sentinel, never zero/open space")
        zones.append(TofZone(distance if valid else None, raw_status))
    return TofSample(sample, rows, columns, tuple(zones))


@dataclass(frozen=True)
class ImuSample:
    sample_id: int
    acceleration: tuple[float, float, float]
    angular_velocity: tuple[float, float, float]
    valid: bool


def decode_imu(payload: bytes) -> ImuSample:
    if len(payload) != IMU.size:
        raise ValueError("invalid IMU length")
    sample, *values, valid = IMU.unpack(payload)
    if valid not in (0, 1) or not all(math.isfinite(value) for value in values):
        raise ValueError("invalid IMU validity/nonfinite number")
    return ImuSample(sample, tuple(values[:3]), tuple(values[3:]), bool(valid))


@dataclass(frozen=True)
class ButtonEvent:
    event_id: int
    button: int
    pressed: bool


def decode_button(payload: bytes) -> ButtonEvent:
    if len(payload) != BUTTON.size:
        raise ValueError("invalid button length")
    event, button, pressed = BUTTON.unpack(payload)
    if button not in (1, 2) or pressed not in (0, 1):
        raise ValueError("unknown physical button/action")
    return ButtonEvent(event, button, bool(pressed))
