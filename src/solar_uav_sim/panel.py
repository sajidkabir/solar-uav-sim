"""Solar panel model: irradiance in, electrical power out."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PanelSpec:
    area_m2: float
    efficiency: float  # 0..1, e.g. 0.22 for a 22% efficient panel
    mppt_efficiency: float = 0.97  # maximum power point tracker losses


def panel_power_w(panel: PanelSpec, irradiance_w_m2: float) -> float:
    """Electrical power output of the panel array in watts."""
    if irradiance_w_m2 <= 0.0:
        return 0.0
    return irradiance_w_m2 * panel.area_m2 * panel.efficiency * panel.mppt_efficiency
