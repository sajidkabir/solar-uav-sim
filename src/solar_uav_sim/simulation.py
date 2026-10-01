"""24-hour energy-balance simulation and the charge-consumption parity solver."""

from __future__ import annotations

from dataclasses import dataclass, field

from .atmosphere import air_density_kg_m3
from .battery import Battery, BatterySpec
from .panel import PanelSpec, panel_power_w
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
    soc: list[float] = field(default_factory=list)
    energy_in_wh: float = 0.0
    energy_out_wh: float = 0.0
    min_soc_wh: float = 0.0
    end_soc_wh: float = 0.0

    @property
    def net_energy_wh(self) -> float:
        return self.energy_in_wh - self.energy_out_wh


def _step_energy(
    config: MissionConfig,
    panel: PanelSpec,
    battery: Battery,
    load_w: float,
    irradiance_scale: float = 1.0,
) -> DayResult:
    rho = air_density_kg_m3(config.altitude_m)
    dt_h = config.dt_minutes / 60.0
    result = DayResult()
    result.min_soc_wh = battery.soc_wh

    t = 0.0
    while t < 24.0:
        irr = clear_sky_irradiance_w_m2(config.latitude_deg, config.day_of_year, t) * irradiance_scale
        solar_w = panel_power_w(panel, irr)

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
        result.soc.append(battery.soc_wh)
        result.min_soc_wh = min(result.min_soc_wh, battery.soc_wh)

        t += dt_h

    result.end_soc_wh = battery.soc_wh
    return result


def run_day(
    config: MissionConfig,
    panel: PanelSpec,
    battery_spec: BatterySpec,
    propulsion: MultirotorSpec,
    irradiance_scale: float = 1.0,
) -> DayResult:
    """Simulate one 24-hour day. Battery starts full; load is hover power."""
    rho = air_density_kg_m3(config.altitude_m)
    load_w = hover_power_w(propulsion, rho)
    battery = Battery(battery_spec)
    return _step_energy(config, panel, battery, load_w, irradiance_scale)


def parity_scale_factor(
    config: MissionConfig,
    panel: PanelSpec,
    battery_spec: BatterySpec,
    propulsion: MultirotorSpec,
    lo: float = 0.0,
    hi: float = 3.0,
    iterations: int = 40,
) -> float:
    """Find the irradiance multiplier at which daily net energy crosses zero.

    A factor of 1.0 means the site's clear-sky day as modeled; 1.2 means 20%
    more solar resource (or equivalently 20% more panel) is needed to break even.
    """
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        net = run_day(config, panel, battery_spec, propulsion, mid).net_energy_wh
        if net >= 0.0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0
