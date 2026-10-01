"""Example: a 3 kg solar quadcopter over Dhaka on the summer solstice."""

from solar_uav_sim import (
    BatterySpec,
    MissionConfig,
    MultirotorSpec,
    PanelSpec,
    parity_scale_factor,
    run_day,
)

config = MissionConfig(latitude_deg=23.8, day_of_year=172, altitude_m=100.0)

panel = PanelSpec(area_m2=1.0, efficiency=0.22)
battery = BatterySpec(capacity_wh=500.0)
propulsion = MultirotorSpec(mass_kg=3.0, num_rotors=4, prop_diameter_m=0.33)

result = run_day(config, panel, battery, propulsion)
print(f"Energy in:  {result.energy_in_wh:.1f} Wh")
print(f"Energy out: {result.energy_out_wh:.1f} Wh")
print(f"Net:        {result.net_energy_wh:.1f} Wh")

factor = parity_scale_factor(config, panel, battery, propulsion)
print(f"Parity factor: {factor:.3f}")
