"""24-hour energy-balance simulation and the charge-consumption parity solver."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .atmosphere import air_density_kg_m3
from .battery import Battery, BatterySpec
from .panel import PanelSpec, panel_power_w
from .profile import DayProfile
from .propulsion import MultirotorSpec, hover_power_w
from .sun import clear_sky_irradiance_w_m2


@dataclass(frozen=True)
class MissionConfig:
    latitude_deg: float
    day_of_year: int
    altitude_m: float = 100.0
    dt_minutes: float = 5.0


@dataclass
class DayResult:
    hours: list[float] = field(default_factory=list)
    irradiance: list[float] = field(default_factory=list)
    solar_power: list[float] = field(default_factory=list)
    load_power: list[float] = field(default_factory=list)
    load_kind: list[str] = field(default_factory=list)
    soc: list[float] = field(default_factory=list)
    energy_in_wh: float = 0.0
    energy_out_wh: float = 0.0
    min_soc_wh: float = 0.0
    end_soc_wh: float = 0.0
    flight_time_s: float = 0.0
    flight_distance_m: float = 0.0

    @property
    def net_energy_wh(self) -> float:
        return self.energy_in_wh - self.energy_out_wh


def _step_energy(
    config: MissionConfig,
    panel: PanelSpec,
    battery: Battery,
    load_fn: Callable[[float], tuple[float, str, float]],
    irradiance_scale: float = 1.0,
) -> DayResult:
    """Integrate one day. load_fn(hour) returns (load_w, kind, speed_m_s)."""
    dt_h = config.dt_minutes / 60.0
    result = DayResult()
    result.min_soc_wh = battery.soc_wh

    # Step-count loop, not accumulated time: adding dt_h 288 times in
    # floating point lands at 23.9999... and runs a 289th step, so the
    # day used to simulate 24h05m and a sortie starting exactly on the
    # hour missed its first step. t is computed from the step index,
    # so hour boundaries land exactly.
    n_steps = int(round(24.0 * 60.0 / config.dt_minutes))
    for i in range(n_steps):
        t = i * config.dt_minutes / 60.0
        irr = clear_sky_irradiance_w_m2(config.latitude_deg, config.day_of_year, t) * irradiance_scale
        solar_w = panel_power_w(panel, irr)
        load_w, kind, speed_m_s = load_fn(t)

        net_w = solar_w - load_w
        result.energy_in_wh += solar_w * dt_h
        result.energy_out_wh += load_w * dt_h
        if net_w >= 0.0:
            battery.charge(net_w, dt_h)
        else:
            battery.discharge(-net_w, dt_h)

        result.hours.append(t)
        result.irradiance.append(irr)
        result.solar_power.append(solar_w)
        result.load_power.append(load_w)
        result.load_kind.append(kind)
        result.soc.append(battery.soc_wh)
        result.min_soc_wh = min(result.min_soc_wh, battery.soc_wh)
        if kind != "ground":
            result.flight_time_s += dt_h * 3600.0
            result.flight_distance_m += speed_m_s * dt_h * 3600.0

    result.end_soc_wh = battery.soc_wh
    return result


def run_day(
    config: MissionConfig,
    panel: PanelSpec,
    battery_spec: BatterySpec,
    propulsion: MultirotorSpec,
    irradiance_scale: float = 1.0,
    profile: DayProfile | None = None,
) -> DayResult:
    """Simulate one 24-hour day. Battery starts full.

    Without a profile the load is hover power all day (the original
    behavior). With a profile the load follows the timed segments and
    is zero on the ground between sorties, so midday sun charges the
    battery instead of fighting a hover load.
    """
    rho = air_density_kg_m3(config.altitude_m)
    battery = Battery(battery_spec)
    if profile is None:
        hover_w = hover_power_w(propulsion, rho)
        return _step_energy(
            config, panel, battery, lambda _hour: (hover_w, "hover", 0.0), irradiance_scale
        )
    return _step_energy(
        config,
        panel,
        battery,
        lambda hour: profile.load_at(hour, propulsion, rho),
        irradiance_scale,
    )


def parity_scale_factor(
    config: MissionConfig,
    panel: PanelSpec,
    battery_spec: BatterySpec,
    propulsion: MultirotorSpec,
    lo: float = 0.0,
    hi: float = 3.0,
    iterations: int = 40,
    profile: DayProfile | None = None,
) -> float:
    """Find the irradiance multiplier at which daily net energy crosses zero.

    A factor of 1.0 means the site's clear-sky day as modeled; 1.2 means 20%
    more solar resource (or equivalently 20% more panel) is needed to break even.

    With a profile, parity is computed for that flying day instead of
    all-day hover, so a sortie plan can be checked against the sun it
    actually gets.

    The search bracket is grown automatically: if the break-even point lies
    beyond the initial ``hi``, the bound is doubled until it brackets the
    root (up to a sanity cap), so the solver never silently saturates at
    the top of the range.
    """
    # Grow the upper bound until it brackets the root (2026-10-09: previously
    # the fixed hi=3.0 silently saturated, e.g. printing 3.000 for a platform
    # whose true parity point sits at 4.22).
    max_hi = 1e4
    while hi < max_hi and run_day(config, panel, battery_spec, propulsion, hi, profile).net_energy_wh < 0.0:
        hi *= 2.0
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        net = run_day(config, panel, battery_spec, propulsion, mid, profile).net_energy_wh
        if net >= 0.0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0
