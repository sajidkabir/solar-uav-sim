"""Timed mission profiles for the 24-hour day simulation.

The day loop used to assume one load all day: hover power, 24 hours.
Real operations fly sorties and sit on the ground in between, charging
from the sun. A DayProfile is a list of timed segments (a start hour
plus a Segment from mission.py); outside the timed windows the
aircraft is on the ground with its systems off, so the load is zero
and any solar power goes into the battery.

Profiles are validated on construction: start hours inside [0, 24),
segments ending no later than hour 24, and no two segments
overlapping. Validation raises ValueError; a bad profile never
silently drops or shifts a sortie.

A profile also changes what the parity solver answers. Parity without
a profile asks "how much sun would all-day hover need"; parity with a
profile asks "how much sun would this actual flying day need", which
is the question an operator planning sorties really has.
"""

from __future__ import annotations

from dataclasses import dataclass

from .mission import Segment, segment_from_dict, segment_power_w
from .propulsion import MultirotorSpec

DAY_HOURS = 24.0


@dataclass(frozen=True)
class TimedSegment:
    """One mission segment placed on the clock: start hour plus segment."""

    start_hour: float
    segment: Segment

    @property
    def end_hour(self) -> float:
        return self.start_hour + self.segment.duration_s / 3600.0


@dataclass(frozen=True)
class DayProfile:
    """A day's flying plan: timed segments, sorted, non-overlapping."""

    segments: tuple[TimedSegment, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.segments, key=lambda item: item.start_hour))
        object.__setattr__(self, "segments", ordered)
        for timed in ordered:
            if timed.segment.kind not in ("hover", "cruise", "climb"):
                raise ValueError(f"unknown segment kind: {timed.segment.kind!r}")
            if not 0.0 <= timed.start_hour < DAY_HOURS:
                raise ValueError(
                    f"segment start hour must be in [0, 24), got {timed.start_hour}"
                )
            if timed.segment.duration_s <= 0.0:
                raise ValueError("segment duration must be > 0")
            if timed.end_hour > DAY_HOURS:
                raise ValueError(
                    f"segment starting at {timed.start_hour} ends after hour 24"
                )
        for earlier, later in zip(ordered, ordered[1:]):
            if later.start_hour < earlier.end_hour:
                raise ValueError(
                    f"segments overlap: {earlier.start_hour}..{earlier.end_hour} "
                    f"and {later.start_hour}..{later.end_hour}"
                )

    def load_at(
        self, hour: float, spec: MultirotorSpec, air_density_kg_m3: float
    ) -> tuple[float, str, float]:
        """Load at one clock hour: (power_w, kind, horizontal speed m/s).

        Kind is "hover", "cruise", or "climb" inside a segment and
        "ground" outside all segments, where power is zero.
        """
        for timed in self.segments:
            if timed.start_hour <= hour < timed.end_hour:
                segment = timed.segment
                power = segment_power_w(spec, air_density_kg_m3, segment)
                speed = segment.speed_m_s if segment.kind == "cruise" else 0.0
                return power, segment.kind, speed
        return 0.0, "ground", 0.0


def profile_from_dicts(data: list[dict]) -> DayProfile:
    """Build a DayProfile from a JSON-style list of dicts.

    Each dict needs start_hour, kind, and duration_s; cruise takes an
    optional speed_m_s and climb an optional climb_rate_m_s, as in
    segment_from_dict.
    """
    if not isinstance(data, list):
        raise ValueError("profile must be a JSON list of segments")
    timed = []
    for item in data:
        timed.append(
            TimedSegment(
                start_hour=float(item["start_hour"]),
                segment=segment_from_dict(item),
            )
        )
    return DayProfile(tuple(timed))
