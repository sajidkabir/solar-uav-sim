"""solar-uav-sim: solar-powered UAV endurance simulation."""

from .simulation import MissionConfig, DayResult, parity_scale_factor, run_day
from .panel import PanelSpec, panel_power_w
from .battery import BatterySpec, Battery
from .mission import (
    MissionResult,
    Segment,
    SegmentResult,
    run_mission,
    segment_from_dict,
    segment_power_w,
)
from .propulsion import (
    MultirotorSpec,
    best_cruise_speed_m_s,
    climb_power_w,
    forward_induced_velocity_m_s,
    forward_power_breakdown_w,
    forward_power_w,
    hover_power_w,
)
from .sun import clear_sky_irradiance_w_m2, solar_altitude_deg, daylight_hours
from .atmosphere import air_density_kg_m3

__version__ = "1.1.0"

__all__ = [
    "MissionConfig",
    "DayResult",
    "parity_scale_factor",
    "run_day",
    "PanelSpec",
    "panel_power_w",
    "BatterySpec",
    "Battery",
    "MissionResult",
    "Segment",
    "SegmentResult",
    "run_mission",
    "segment_from_dict",
    "segment_power_w",
    "MultirotorSpec",
    "best_cruise_speed_m_s",
    "climb_power_w",
    "forward_induced_velocity_m_s",
    "forward_power_breakdown_w",
    "forward_power_w",
    "hover_power_w",
    "clear_sky_irradiance_w_m2",
    "solar_altitude_deg",
    "daylight_hours",
    "air_density_kg_m3",
]
