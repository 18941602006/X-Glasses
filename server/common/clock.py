"""Four-timestamp clock estimate with explicit uncertainty and expiry, not calibration."""

from collections import deque
from dataclasses import dataclass

MAX_RTT_NS = 100_000_000
CLOCK_TTL_NS = 5_000_000_000
DRIFT_PPM_BUDGET = 200  # Unmeasured design budget, never a measured oscillator guarantee.


@dataclass(frozen=True)
class TimeEstimate:
    host_ns: int
    uncertainty_ns: int


class ClockMapper:
    def __init__(self):
        self.samples = deque(maxlen=8)

    def reset(self):
        self.samples.clear()

    def observe(self, host_send_ns, device_receive_us, device_send_us, host_receive_ns):
        times = (host_send_ns, device_receive_us, device_send_us, host_receive_ns)
        if any(not isinstance(value, int) or not 0 <= value < 2**64 for value in times):
            raise ValueError("clock values must be uint64 integers")
        if host_receive_ns < host_send_ns or device_send_us < device_receive_us:
            raise ValueError("clock exchange moved backwards")
        processing = (device_send_us - device_receive_us) * 1000
        rtt = host_receive_ns - host_send_ns - processing
        if not 0 <= rtt <= MAX_RTT_NS:
            raise ValueError("clock RTT outside budget")
        if self.samples and host_receive_ns < self.samples[-1][0]:
            raise ValueError("clock observations moved backwards")
        offset = (host_send_ns + host_receive_ns - (device_receive_us + device_send_us) * 1000) // 2
        if self.samples and host_receive_ns - self.samples[-1][0] < CLOCK_TTL_NS:
            previous_ns, previous_offset, previous_error = self.samples[-1]
            budget = previous_error + rtt // 2 + 2000
            budget += (host_receive_ns - previous_ns) * DRIFT_PPM_BUDGET // 1_000_000
            if abs(offset - previous_offset) > budget:
                self.reset()
                raise ValueError("clock discontinuity exceeds assumed drift/error budget")
        # Device microsecond quantization and rounding included; asymmetry bounded by RTT/2.
        self.samples.append((host_receive_ns, offset, rtt // 2 + 2000))

    def _best(self, now_ns):
        candidates = [sample for sample in self.samples if 0 <= now_ns - sample[0] < CLOCK_TTL_NS]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda sample: sample[2] + (now_ns - sample[0]) * DRIFT_PPM_BUDGET // 1_000_000,
        )

    def map(self, device_us, now_ns) -> TimeEstimate | None:
        sample = self._best(now_ns)
        if sample is None or not 0 <= device_us < 2**64:
            return None
        observed, offset, uncertainty = sample
        mapped = device_us * 1000 + offset
        if mapped < 0:
            return None
        return TimeEstimate(
            mapped, uncertainty + (now_ns - observed) * DRIFT_PPM_BUDGET // 1_000_000
        )

    def is_ready(self, now_ns):
        return self._best(now_ns) is not None

    def device_deadline(self, now_ns, duration_ns):
        sample = self._best(now_ns)
        if sample is None or duration_ns <= 0:
            raise ValueError("fresh clock estimate required")
        observed, offset, uncertainty = sample
        uncertainty += (now_ns - observed) * DRIFT_PPM_BUDGET // 1_000_000
        # Conservative early deadline; uncertainty cannot extend an actuator command.
        deadline = (now_ns + duration_ns - offset - uncertainty) // 1000
        if deadline <= 0 or uncertainty >= duration_ns or deadline >= 2**64:
            raise ValueError("clock uncertainty exceeds command lifetime")
        return deadline
