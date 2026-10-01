"""solar-uav-sim: solar-powered UAV endurance simulation."""

from .simulation import MissionConfig, DayResult, parity_scale_factor, run_day
from .panel import PanelSpec, panel_power_w
from .battery import BatterySpec, Battery
from .propulsion import MultirotorSpec, hover_power_w, climb_power_w
from .sun import clear_sky_irradiance_w_m2, solar_altitude_deg, daylight_hours
from .atmosphere import air_density_kg_m3

__version__ = "0.1.0"

__all__ = [
    "MissionConfig",
    "DayResult",
    "parity_scale_factor",
    "run_day",
    "PanelSpec",
    "panel_power_w",
    "BatterySpec",
    "Battery",
    "MultirotorSpec",
    "hover_power_w",
    "climb_power_w",
    "clear_sky_irradiance_w_m2",
    "solar_altitude_deg",
    "daylight_hours",
    "air_density_kg_m3",
]
