import math

from solar_uav_sim import (
    clear_sky_irradiance_w_m2,
    daylight_hours,
    solar_altitude_deg,
)


def test_solar_noon_near_zenith_at_equator_on_equinox():
    alt = solar_altitude_deg(0.0, 80, 12.0)
    assert 85.0 < alt <= 90.0


def test_midnight_irradiance_is_zero():
    assert clear_sky_irradiance_w_m2(23.8, 172, 0.0) == 0.0


def test_noon_irradiance_positive():
    assert clear_sky_irradiance_w_m2(23.8, 172, 12.0) > 500.0


def test_daylight_hours_equator_equinox_about_12():
    assert abs(daylight_hours(0.0, 80) - 12.0) < 0.2
