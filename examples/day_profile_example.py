"""A flying day with timed sorties, priced inside the 24-hour loop.

The same 3 kg quad over Dhaka on the solstice, flown as a morning
survey cruise, a midday hover inspection, and an afternoon transit,
instead of hovering all day. Compare the two days: the profile day
draws far less energy and ends with a fuller battery, because the
aircraft sits on the ground charging through the midday sun.
"""

from solar_uav_sim import (
    BatterySpec,
    MissionConfig,
    MultirotorSpec,
    PanelSpec,
    profile_from_dicts,
    run_day,
)

config = MissionConfig(latitude_deg=23.8, day_of_year=172)
panel = PanelSpec(area_m2=1.0, efficiency=0.22)
battery = BatterySpec(capacity_wh=500.0)
propulsion = MultirotorSpec(mass_kg=3.0, num_rotors=4, prop_diameter_m=0.33)

hover_day = run_day(config, panel, battery, propulsion)

profile = profile_from_dicts(
    [
        {"start_hour": 6.0, "kind": "cruise", "duration_s": 3600, "speed_m_s": 12.0},
        {"start_hour": 12.0, "kind": "hover", "duration_s": 600},
        {"start_hour": 16.0, "kind": "cruise", "duration_s": 1800, "speed_m_s": 15.0},
    ]
)
profile_day = run_day(config, panel, battery, propulsion, profile=profile)

for label, result in (("All-day hover", hover_day), ("Profile day  ", profile_day)):
    print(
        f"{label}: in {result.energy_in_wh:7.1f} Wh, out {result.energy_out_wh:7.1f} Wh, "
        f"net {result.net_energy_wh:8.1f} Wh, end SoC {result.end_soc_wh:6.1f} Wh, "
        f"flown {result.flight_time_s:.0f} s over {result.flight_distance_m / 1000:.1f} km"
    )
