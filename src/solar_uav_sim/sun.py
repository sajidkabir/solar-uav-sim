"""Solar position and clear-sky irradiance model."""

from __future__ import annotations

import math

SOLAR_CONSTANT_W_M2 = 1361.0
CLEAR_SKY_TRANSMITTANCE = 0.7


def solar_declination_deg(day_of_year: int) -> float:
    """Solar declination angle in degrees (Cooper's equation)."""
    return -23.44 * math.cos(2.0 * math.pi * (day_of_year + 10) / 365.0)


def hour_angle_deg(hour: float) -> float:
    """Solar hour angle in degrees; 0 at solar noon."""
    return 15.0 * (hour - 12.0)


def solar_altitude_deg(latitude_deg: float, day_of_year: int, hour: float) -> float:
    """Solar altitude angle above the horizon, in degrees."""
    lat = math.radians(latitude_deg)
    dec = math.radians(solar_declination_deg(day_of_year))
    ha = math.radians(hour_angle_deg(hour))
    sin_alt = math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(ha)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    return math.degrees(math.asin(sin_alt))


def clear_sky_irradiance_w_m2(latitude_deg: float, day_of_year: int, hour: float) -> float:
    """Global horizontal irradiance under a clear sky, W/m^2.

    Simple model: extraterrestrial irradiance scaled by sin(altitude) and a
    bulk atmospheric transmittance raised to the relative air mass.
    """
    alt_deg = solar_altitude_deg(latitude_deg, day_of_year, hour)
    if alt_deg <= 0.0:
        return 0.0
    alt_rad = math.radians(alt_deg)
    air_mass = 1.0 / math.sin(alt_rad)
    return SOLAR_CONSTANT_W_M2 * math.sin(alt_rad) * (CLEAR_SKY_TRANSMITTANCE ** (air_mass ** 0.678))


def daylight_hours(latitude_deg: float, day_of_year: int) -> float:
    """Day length in hours from sunrise to sunset."""
    lat = math.radians(latitude_deg)
    dec = math.radians(solar_declination_deg(day_of_year))
    cos_h0 = -math.tan(lat) * math.tan(dec)
    cos_h0 = max(-1.0, min(1.0, cos_h0))
    return 2.0 * math.degrees(math.acos(cos_h0)) / 15.0
