"""Battery model with charge/discharge efficiency and depth-of-discharge limit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BatterySpec:
    capacity_wh: float
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.97
    max_depth_of_discharge: float = 0.8  # fraction of capacity usable


class Battery:
    def __init__(self, spec: BatterySpec, initial_soc_wh: float | None = None):
        self.spec = spec
        self.soc_wh = spec.capacity_wh if initial_soc_wh is None else initial_soc_wh

    @property
    def usable_capacity_wh(self) -> float:
        return self.spec.capacity_wh * self.spec.max_depth_of_discharge

    def charge(self, power_w: float, dt_h: float) -> float:
        """Push power into the battery for dt_h hours. Returns energy stored (Wh)."""
        if power_w <= 0.0 or dt_h <= 0.0:
            return 0.0
        stored = power_w * dt_h * self.spec.charge_efficiency
        room = self.spec.capacity_wh - self.soc_wh
        stored = min(stored, room)
        self.soc_wh += stored
        return stored

    def discharge(self, power_w: float, dt_h: float) -> float:
        """Draw power from the battery for dt_h hours. Returns energy delivered (Wh)."""
        if power_w <= 0.0 or dt_h <= 0.0:
            return 0.0
        drawn = power_w * dt_h / self.spec.discharge_efficiency
        floor = self.spec.capacity_wh * (1.0 - self.spec.max_depth_of_discharge)
        drawn = min(drawn, self.soc_wh - floor)
        drawn = max(0.0, drawn)
        self.soc_wh -= drawn
        return drawn * self.spec.discharge_efficiency
