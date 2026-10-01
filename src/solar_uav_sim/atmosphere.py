"""Simple ISA air-density model (troposphere, up to 11 km)."""

from __future__ import annotations

T0_K = 288.15
P0_PA = 101325.0
LAPSE_RATE_K_M = 0.0065
R_SPECIFIC = 287.05


def air_density_kg_m3(altitude_m: float) -> float:
    """Air density in kg/m^3 at the given altitude above sea level."""
    h = max(0.0, altitude_m)
    t = T0_K - LAPSE_RATE_K_M * h
    p = P0_PA * (t / T0_K) ** 5.25588
    return p / (R_SPECIFIC * t)
