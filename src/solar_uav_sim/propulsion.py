"""Multirotor propulsion power model (momentum theory for hover)."""

from __future__ import annotations

import math
from dataclasses import dataclass

G = 9.81


@dataclass(frozen=True)
class MultirotorSpec:
    mass_kg: float
    num_rotors: int
    prop_diameter_m: float
    figure_of_merit: float = 0.65  # real rotor vs ideal induced power
    avionics_w: float = 5.0  # flight controller, receiver, telemetry


def hover_power_w(spec: MultirotorSpec, air_density_kg_m3: float) -> float:
    """Electrical hover power in watts from actuator-disk momentum theory.

    Induced power per rotor: P = T^1.5 / sqrt(2 * rho * A), corrected by
    the figure of merit, plus avionics base load.
    """
    thrust_per_rotor_n = spec.mass_kg * G / spec.num_rotors
    disk_area_m2 = math.pi * (spec.prop_diameter_m / 2.0) ** 2
    p_induced = (thrust_per_rotor_n ** 1.5) / math.sqrt(2.0 * air_density_kg_m3 * disk_area_m2)
    return spec.num_rotors * p_induced / spec.figure_of_merit + spec.avionics_w


def climb_power_w(spec: MultirotorSpec, air_density_kg_m3: float, climb_rate_m_s: float) -> float:
    """Hover power plus the power needed to climb at the given rate."""
    return hover_power_w(spec, air_density_kg_m3) + spec.mass_kg * G * max(0.0, climb_rate_m_s)
