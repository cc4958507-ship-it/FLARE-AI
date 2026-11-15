"""Educational synthetic profile. No physical units or safety certification."""
from dataclasses import dataclass, field, asdict
from enum import StrEnum
import random
import math


class Action(StrEnum):
    REDUCE = "SIM_REDUCE_SOURCE"
    STOP = "SIM_STOP_SOURCE"


@dataclass(frozen=True)
class Event:
    t: int
    action: Action


@dataclass(frozen=True)
class Sample:
    t: int
    flame_presence: float | None
    thermal_excess: float | None
    co_proxy: float | None
    ventilation_proxy: float | None
    co2_proxy: float | None
    unit: str = "sim_unit"
    quality_flags: tuple[str, ...] = ()


REQUIRED = ("flame_presence", "thermal_excess", "co_proxy", "ventilation_proxy")


def generate(seed: int, duration: int, events: list[Event], fault_at: int | None = None, faults=None):
    rng = random.Random(seed)
    source, thermal, co, co2 = 1.0, 0.7, 0.3, 0.6
    observations = []
    for t in range(duration + 1):
        for event in events:
            if event.t == t:
                source *= 0.45 if event.action == Action.REDUCE else 0.0
        thermal = max(0, thermal + 0.09 * source - 0.12 * thermal)
        co = max(0, co + 0.06 * source - 0.04 * co)
        co2 = max(0, co2 + 0.04 * source - 0.012 * co2)
        noise = lambda value: max(0.0, min(1.0, value + rng.uniform(-0.0002, 0.0002)))
        sample = Sample(t, float(source > 0.5), noise(thermal),
                     None if fault_at is not None and t >= fault_at else noise(co),
                     1.0, noise(co2))
        values = asdict(sample)
        flags = []
        for fault in faults or []:
            if t < fault['t']:
                continue
            channel, kind = fault['channel'], fault['fault']
            flags.append(channel + ':' + kind)
            if kind == 'drop':
                values[channel] = None
            elif kind in ('freeze', 'replay'):
                at = max(0, fault['t'] - (1 if kind == 'freeze' else 5))
                values[channel] = observations[at][channel] if at < len(observations) else None
            elif kind == 'saturation':
                values[channel] = 1.0
            elif kind == 'skew':
                values[channel] = None
        values['quality_flags'] = tuple(flags)
        observations.append(values)
        yield Sample(**values)


@dataclass
class Verifier:
    history: list[Sample] = field(default_factory=list)
    latched: bool = False
    clear_since: int | None = None
    hold_since: int | None = None
    rising_since: int | None = None
    verified_at: int | None = None

    def evaluate(self, sample: Sample, context_changed: bool = False, scope: str = "synthetic-v1"):
        if self.history and sample.t <= self.history[-1].t:
            raise ValueError("Samples must have strictly increasing timestamps")
        self.history.append(sample)
        window = [s for s in self.history if s.t >= sample.t - 10]
        valid = all(not s.quality_flags and all(
            getattr(s, c) is not None and math.isfinite(getattr(s, c))
            and 0 <= getattr(s, c) <= 1 for c in REQUIRED) for s in window)
        coverage = len(window) >= 11 and all(b.t - a.t <= 2 for a, b in zip(window, window[1:]))
        quality = valid and coverage
        slopes = {}
        for channel in ("thermal_excess", "co_proxy"):
            points = [(s.t, getattr(s, channel)) for s in window if getattr(s, channel) is not None]
            if len(points) >= 2:
                slopes[channel] = (points[-1][1] - points[0][1]) / (points[-1][0] - points[0][0])
        rising = (quality and slopes.get("co_proxy", 0) > 0.01
                  and sample.thermal_excess > 0.30)
        self.rising_since = (sample.t if self.rising_since is None else self.rising_since) if rising else None
        danger = sample.flame_presence == 1 or (self.rising_since is not None and sample.t - self.rising_since >= 3)
        clear = (quality and scope == "synthetic-v1" and not context_changed
                 and sample.flame_presence == 0 and sample.thermal_excess <= 0.25
                 and sample.co_proxy <= 0.20 and all(v <= 0.002 for v in slopes.values()))
        reason = []
        if danger:
            self.latched = True
            self.clear_since = self.hold_since = None
            status = "Danger"
            reason = ["VALID_POSITIVE_DANGER"]
        elif self.latched:
            self.hold_since = None
            self.clear_since = (sample.t if self.clear_since is None else self.clear_since) if clear else None
            if self.clear_since is not None and sample.t - self.clear_since >= 10:
                self.latched = False
                self.hold_since = sample.t
                status, reason = "Uncertain", ["DANGER_CLEARED_HOLD_STARTED"]
            else:
                status = "Danger"
                reason = ["DANGER_LATCHED" if quality else "DANGER_LATCHED_DATA_LOSS"]
        elif clear:
            self.hold_since = sample.t if self.hold_since is None else self.hold_since
            status = "Verified" if sample.t - self.hold_since >= 30 else "Uncertain"
            reason = ["HOLD_COMPLETE" if status == "Verified" else "HOLD_IN_PROGRESS"]
        else:
            self.hold_since = None
            status, reason = "Uncertain", ["CLEARANCE_NOT_MET" if quality else "REQUIRED_DATA_INVALID_OR_WARMUP"]
        if status == "Verified" and self.verified_at is None:
            self.verified_at = sample.t
        return {"t": sample.t, "combustion_status": status,
                "label": "Verified within simulated conditions" if status == "Verified" else status,
                "atmosphere_status": "elevated" if (sample.co2_proxy or 0) > 0.2 else "declining",
                "data_integrity": "valid" if valid else "invalid", "required_quality": "valid" if quality else "invalid",
                "reason_codes": reason, "features": slopes, "profile": "synthetic-v1",
                "engine_version": "0.1.0", "verified_at": self.verified_at,
                "hold_elapsed_s": sample.t - self.hold_since if self.hold_since is not None else 0,
                "window_start": window[0].t, "window_end": sample.t,
                "required_channels": REQUIRED, "provenance": "synthetic"}


def replay(seed: int, duration: int, events: list[Event], fault_at: int | None = None, faults=None):
    verifier = Verifier()
    samples, decisions = [], []
    for sample in generate(seed, duration, events, fault_at, faults):
        samples.append(asdict(sample))
        decisions.append(verifier.evaluate(sample, any(e.t == sample.t for e in events)))
    return {"samples": samples, "decisions": decisions}
