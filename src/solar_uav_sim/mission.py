"""Segment-based mission energy: mix hover, cruise, and climb segments.

The 24-hour day simulation in simulation.py assumes an all-day hover
load. Real missions do not hover all day, so this module prices a timed
segment list instead: each segment has a kind, a duration, and (for
cruise) a forward speed or (for climb) a climb rate. Summing segment
energies gives the mission's total energy draw, distance covered, and
average power, which is the number a battery sizing decision actually
needs.

Segment kinds:

- "hover": stationary, power from hover_power_w.
- "cruise": level forward flight at speed_m_s, power from forward_power_w.
- "climb": vertical climb at climb_rate_m_s, power from climb_power_w
  (hover power plus m * g * climb rate; descent is priced as hover,
  matching climb_power_w, since a multirotor does not recover energy
  descending).

Unknown kinds, non-positive durations, negative speeds, and negative
climb rates are rejected with ValueError rather than silently priced.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .propulsion import MultirotorSpec, climb_power_w, forward_power_w, hover_power_w


@dataclass(frozen=True)
class Segment:
    kind: str  # "hover", "cruise", or "climb"
    duration_s: float
    speed_m_s: float = 0.0  # cruise only
    climb_rate_m_s: float = 0.0  # climb only


@dataclass
class SegmentResult:
    kind: str
    duration_s: float
    power_w: float
    energy_wh: float
    distance_m: float = 0.0  # horizontal distance (cruise only)
    vertical_m: float = 0.0  # climb only


@dataclass
class MissionResult:
    segments: list[SegmentResult] = field(default_factory=list)
    total_energy_wh: float = 0.0
    total_time_s: float = 0.0
    total_distance_m: float = 0.0

    @property
    def average_power_w(self) -> float:
        if self.total_time_s <= 0.0:
            return 0.0
        return self.total_energy_wh * 3600.0 / self.total_time_s


def segment_power_w(spec: MultirotorSpec, air_density_kg_m3: float, segment: Segment) -> float:
    """Electrical power for one segment (watts)."""
    if segment.duration_s <= 0.0:
        raise ValueError("segment duration must be > 0")
    if segment.kind == "hover":
        return hover_power_w(spec, air_density_kg_m3)
    if segment.kind == "cruise":
        if segment.speed_m_s < 0.0:
            raise ValueError("cruise speed must be >= 0")
        return forward_power_w(spec, air_density_kg_m3, segment.speed_m_s)
    if segment.kind == "climb":
        if segment.climb_rate_m_s < 0.0:
            raise ValueError("climb rate must be >= 0")
        return climb_power_w(spec, air_density_kg_m3, segment.climb_rate_m_s)
    raise ValueError(f"unknown segment kind: {segment.kind!r}")


def run_mission(
    spec: MultirotorSpec, air_density_kg_m3: float, segments: list[Segment]
) -> MissionResult:
    """Price a whole mission: total energy, time, and distance."""
    if not segments:
        raise ValueError("mission must contain at least one segment")
    result = MissionResult()
    for segment in segments:
        power = segment_power_w(spec, air_density_kg_m3, segment)
        energy_wh = power * segment.duration_s / 3600.0
        distance_m = segment.speed_m_s * segment.duration_s if segment.kind == "cruise" else 0.0
        vertical_m = segment.climb_rate_m_s * segment.duration_s if segment.kind == "climb" else 0.0
        result.segments.append(
            SegmentResult(
                kind=segment.kind,
                duration_s=segment.duration_s,
                power_w=power,
                energy_wh=energy_wh,
                distance_m=distance_m,
                vertical_m=vertical_m,
            )
        )
        result.total_energy_wh += energy_wh
        result.total_time_s += segment.duration_s
        result.total_distance_m += distance_m
    return result


def segment_from_dict(data: dict) -> Segment:
    """Build a Segment from a JSON-style dict.

    Required keys: kind, duration_s. Optional: speed_m_s, climb_rate_m_s.
    """
    return Segment(
        kind=data["kind"],
        duration_s=float(data["duration_s"]),
        speed_m_s=float(data.get("speed_m_s", 0.0)),
        climb_rate_m_s=float(data.get("climb_rate_m_s", 0.0)),
    )
