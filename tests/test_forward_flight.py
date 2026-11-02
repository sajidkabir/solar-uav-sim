import math

import pytest

from solar_uav_sim import (
    MultirotorSpec,
    air_density_kg_m3,
    best_cruise_speed_m_s,
    forward_induced_velocity_m_s,
    forward_power_breakdown_w,
    forward_power_w,
    hover_power_w,
)


def _spec(mass_kg=3.0):
    return MultirotorSpec(mass_kg=mass_kg, num_rotors=4, prop_diameter_m=0.33)


def test_forward_power_at_zero_speed_is_hover_power():
    # Calibration invariant: the forward model must not move the
    # validated hover numbers.
    spec = _spec()
    rho = air_density_kg_m3(100.0)
    assert forward_power_w(spec, rho, 0.0) == hover_power_w(spec, rho)


def test_induced_velocity_falls_with_speed():
    spec = _spec()
    rho = air_density_kg_m3(0.0)
    v_hover = forward_induced_velocity_m_s(spec, rho, 0.0)
    v_10 = forward_induced_velocity_m_s(spec, rho, 10.0)
    v_20 = forward_induced_velocity_m_s(spec, rho, 20.0)
    assert v_hover > v_10 > v_20 > 0.0
    # Hand check: hover induced velocity from momentum theory.
    thrust_per_rotor = 3.0 * 9.81 / 4.0
    area = math.pi * (0.33 / 2.0) ** 2
    assert v_hover == pytest.approx(math.sqrt(thrust_per_rotor / (2.0 * rho * area)), rel=1e-9)
    # High-speed asymptote: v_i tends to v_h^2 / V.
    v_40 = forward_induced_velocity_m_s(spec, rho, 40.0)
    assert v_40 == pytest.approx(v_hover * v_hover / 40.0, rel=0.05)


def test_power_curve_is_u_shaped():
    # Translational lift first beats hover, then drag takes over.
    spec = _spec()
    rho = air_density_kg_m3(0.0)
    hover = hover_power_w(spec, rho)
    p5 = forward_power_w(spec, rho, 5.0)
    p10 = forward_power_w(spec, rho, 10.0)
    p15 = forward_power_w(spec, rho, 15.0)
    p30 = forward_power_w(spec, rho, 30.0)
    assert hover > p5 > p10 > p15
    assert p30 > hover


def test_breakdown_sums_and_parasite_formula():
    spec = _spec()
    rho = air_density_kg_m3(0.0)
    breakdown = forward_power_breakdown_w(spec, rho, 15.0)
    assert breakdown["total"] == pytest.approx(
        breakdown["induced"] + breakdown["profile_increment"]
        + breakdown["parasite"] + breakdown["avionics"]
    )
    # Parasite term, independently: 0.5 * rho * CdA * V^3 / eta.
    expected_parasite = 0.5 * rho * spec.drag_area_m2 * 15.0 ** 3 / spec.drivetrain_efficiency
    assert breakdown["parasite"] == pytest.approx(expected_parasite, rel=1e-9)
    # Profile increment is zero at hover and grows with speed.
    assert forward_power_breakdown_w(spec, rho, 0.0)["profile_increment"] == 0.0
    assert breakdown["profile_increment"] > 0.0
    assert forward_power_breakdown_w(spec, rho, 20.0)["profile_increment"] > breakdown["profile_increment"]


def test_best_cruise_speed_is_a_real_minimum():
    spec = _spec()
    rho = air_density_kg_m3(0.0)
    speed, power = best_cruise_speed_m_s(spec, rho)
    assert 5.0 < speed < 25.0
    assert power < hover_power_w(spec, rho)
    assert power <= forward_power_w(spec, rho, 30.0)
    assert power <= forward_power_w(spec, rho, 0.0)


def test_forward_power_scales_like_hover():
    light, heavy = _spec(2.0), _spec(4.0)
    rho = air_density_kg_m3(0.0)
    assert forward_power_w(heavy, rho, 12.0) > forward_power_w(light, rho, 12.0)
    spec = _spec()
    assert forward_power_w(spec, air_density_kg_m3(3000.0), 10.0) > forward_power_w(
        spec, air_density_kg_m3(0.0), 10.0
    )


def test_invalid_forward_inputs_rejected():
    spec = _spec()
    rho = air_density_kg_m3(0.0)
    with pytest.raises(ValueError):
        forward_power_w(spec, rho, -1.0)
    with pytest.raises(ValueError):
        forward_power_w(spec, 0.0, 10.0)
    with pytest.raises(ValueError):
        forward_induced_velocity_m_s(spec, rho, -5.0)
    with pytest.raises(ValueError):
        best_cruise_speed_m_s(spec, rho, 0.0)
