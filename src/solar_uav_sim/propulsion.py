"""Multirotor propulsion power model: hover, climb, and forward flight.

Hover and climb come from actuator-disk momentum theory. Forward flight
adds the three terms every multirotor energy model needs:

- induced power, which FALLS with forward speed (translational lift: the
  rotor works in cleaner air, so the induced velocity drops);
- profile power, which RISES with speed through the advance ratio
  (blade-element factor 1 + 3 mu^2, mu = V / tip speed);
- parasite power, the airframe drag term, which grows with V^3 and
  dominates at high speed.

The result is the classic U-shaped power curve: a multirotor cruises
cheaper than it hovers, up to a minimum-power speed, after which drag
takes over. One deliberate calibration choice keeps the validated hover
numbers intact: the hover model already absorbs profile power at hover
inside its figure of merit (it was calibrated to the DJI Mavic 3 spec
point), so the forward model adds only the profile INCREMENT above
hover, not a second full profile term. At zero speed, forward power is
therefore exactly the hover power, by construction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

G = 9.81


@dataclass(frozen=True)
class MultirotorSpec:
    mass_kg: float
    num_rotors: int
    prop_diameter_m: float
    figure_of_merit: float = 0.55  # real rotor vs ideal induced power
    drivetrain_efficiency: float = 0.65  # motor + ESC electrical efficiency
    avionics_w: float = 5.0  # flight controller, receiver, telemetry
    # Forward-flight parameters (defaults are typical small-quad values,
    # documented as estimates, not calibrated to a specific airframe):
    drag_area_m2: float = 0.03  # equivalent flat-plate area Cd*A
    tip_speed_m_s: float = 90.0  # rotor tip speed at hover RPM
    blade_solidity: float = 0.08  # rotor solidity sigma
    profile_drag_coeff: float = 0.012  # blade-section profile drag Cd0


def _disk_area_m2(spec: MultirotorSpec) -> float:
    return math.pi * (spec.prop_diameter_m / 2.0) ** 2


def _hover_induced_velocity_m_s(spec: MultirotorSpec, air_density_kg_m3: float) -> float:
    """Hover induced velocity from momentum theory, per rotor."""
    thrust_per_rotor_n = spec.mass_kg * G / spec.num_rotors
    return math.sqrt(thrust_per_rotor_n / (2.0 * air_density_kg_m3 * _disk_area_m2(spec)))


def hover_power_w(spec: MultirotorSpec, air_density_kg_m3: float) -> float:
    """Electrical hover power in watts from actuator-disk momentum theory.

    Induced power per rotor: P = T^1.5 / sqrt(2 * rho * A), corrected by
    the rotor figure of merit and the motor/controller drivetrain efficiency,
    plus avionics base load.

    Default efficiencies are calibrated (2026-10-09) so the model reproduces
    the DJI Mavic 3 spec point: 0.895 kg, 77.0 Wh battery, 40 min hover
    (no wind) -> 115.5 W electrical, treated as a lower bound on true hover
    power because manufacturer times are optimistic no-wind figures.
    See validation/check3_hover_power.py.
    """
    thrust_per_rotor_n = spec.mass_kg * G / spec.num_rotors
    disk_area_m2 = _disk_area_m2(spec)
    p_induced = (thrust_per_rotor_n ** 1.5) / math.sqrt(2.0 * air_density_kg_m3 * disk_area_m2)
    return (
        spec.num_rotors * p_induced
        / spec.figure_of_merit
        / spec.drivetrain_efficiency
        + spec.avionics_w
    )


def climb_power_w(spec: MultirotorSpec, air_density_kg_m3: float, climb_rate_m_s: float) -> float:
    """Hover power plus the power needed to climb at the given rate."""
    return hover_power_w(spec, air_density_kg_m3) + spec.mass_kg * G * max(0.0, climb_rate_m_s)


def forward_induced_velocity_m_s(spec: MultirotorSpec, air_density_kg_m3: float, speed_m_s: float) -> float:
    """Induced velocity in level forward flight (Glauert momentum theory).

    Solves v_i = v_h^2 / sqrt(V^2 + v_i^2) by fixed-point iteration, where
    v_h is the hover induced velocity. At V = 0 this returns v_h exactly;
    at high speed it tends to v_h^2 / V. Raises ValueError for negative
    speed or non-positive density.
    """
    if speed_m_s < 0.0:
        raise ValueError("forward speed must be >= 0")
    if air_density_kg_m3 <= 0.0:
        raise ValueError("air density must be > 0")
    v_h = _hover_induced_velocity_m_s(spec, air_density_kg_m3)
    if speed_m_s == 0.0:
        return v_h
    v_i = v_h
    for _ in range(200):
        nxt = v_h * v_h / math.sqrt(speed_m_s * speed_m_s + v_i * v_i)
        if abs(nxt - v_i) < 1e-9:
            return nxt
        v_i = nxt
    return v_i


def _profile_power_elec_w(spec: MultirotorSpec, air_density_kg_m3: float, speed_m_s: float) -> float:
    """Electrical profile power from blade-element theory.

    Per rotor: P = (sigma * Cd0 / 8) * rho * A * V_tip^3 * (1 + 3 mu^2),
    summed over rotors and divided by drivetrain efficiency. This is the
    FULL profile term; forward_power_w uses only its increment above
    hover (see module docstring).
    """
    if spec.tip_speed_m_s <= 0.0:
        raise ValueError("tip speed must be > 0")
    mu = speed_m_s / spec.tip_speed_m_s
    per_rotor_shaft = (
        (spec.blade_solidity * spec.profile_drag_coeff / 8.0)
        * air_density_kg_m3
        * _disk_area_m2(spec)
        * spec.tip_speed_m_s ** 3
        * (1.0 + 3.0 * mu * mu)
    )
    return spec.num_rotors * per_rotor_shaft / spec.drivetrain_efficiency


def forward_power_breakdown_w(spec: MultirotorSpec, air_density_kg_m3: float, speed_m_s: float) -> dict:
    """Electrical forward-flight power split into its four terms (watts).

    Keys: induced, profile_increment, parasite, avionics, total. At zero
    speed, induced equals the hover induced term and the other speed
    terms are zero, so total equals hover_power_w exactly.
    """
    if speed_m_s < 0.0:
        raise ValueError("forward speed must be >= 0")
    if air_density_kg_m3 <= 0.0:
        raise ValueError("air density must be > 0")
    v_i = forward_induced_velocity_m_s(spec, air_density_kg_m3, speed_m_s)
    induced = spec.mass_kg * G * v_i / spec.figure_of_merit / spec.drivetrain_efficiency
    profile_increment = (
        _profile_power_elec_w(spec, air_density_kg_m3, speed_m_s)
        - _profile_power_elec_w(spec, air_density_kg_m3, 0.0)
    )
    parasite = 0.5 * air_density_kg_m3 * spec.drag_area_m2 * speed_m_s ** 3 / spec.drivetrain_efficiency
    total = induced + profile_increment + parasite + spec.avionics_w
    return {
        "induced": induced,
        "profile_increment": profile_increment,
        "parasite": parasite,
        "avionics": spec.avionics_w,
        "total": total,
    }


def forward_power_w(spec: MultirotorSpec, air_density_kg_m3: float, speed_m_s: float) -> float:
    """Electrical power in level forward flight at the given speed (watts)."""
    return forward_power_breakdown_w(spec, air_density_kg_m3, speed_m_s)["total"]


def best_cruise_speed_m_s(
    spec: MultirotorSpec, air_density_kg_m3: float, max_speed_m_s: float = 40.0
) -> tuple[float, float]:
    """Minimum-power cruise speed and its power, by a 0.25 m/s scan.

    Returns (speed_m_s, power_w). The scan is coarse by design: it finds
    the bottom of the U-shaped curve, not a control-system setpoint.
    """
    if max_speed_m_s <= 0.0:
        raise ValueError("max speed must be > 0")
    best_speed = 0.0
    best_power = forward_power_w(spec, air_density_kg_m3, 0.0)
    steps = int(max_speed_m_s / 0.25)
    for i in range(1, steps + 1):
        speed = i * 0.25
        power = forward_power_w(spec, air_density_kg_m3, speed)
        if power < best_power:
            best_speed, best_power = speed, power
    return best_speed, best_power
