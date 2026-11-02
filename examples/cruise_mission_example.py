"""Example: forward-flight power curve and a mixed hover/cruise/climb mission."""

from solar_uav_sim import (
    MultirotorSpec,
    Segment,
    air_density_kg_m3,
    best_cruise_speed_m_s,
    forward_power_w,
    hover_power_w,
    run_mission,
)

spec = MultirotorSpec(mass_kg=3.0, num_rotors=4, prop_diameter_m=0.33)
rho = air_density_kg_m3(100.0)

print("Forward-flight power curve (3 kg quad, 100 m altitude):")
for speed in (0, 5, 10, 15, 20, 25, 30):
    print(f"  {speed:2d} m/s: {forward_power_w(spec, rho, float(speed)):6.1f} W")
best_speed, best_power = best_cruise_speed_m_s(spec, rho)
print(f"Hover power: {hover_power_w(spec, rho):.1f} W")
print(f"Minimum-power cruise: {best_speed:.2f} m/s at {best_power:.1f} W")

mission = run_mission(
    spec,
    rho,
    [
        Segment("hover", 600.0),
        Segment("cruise", 1200.0, speed_m_s=best_speed),
        Segment("climb", 60.0, climb_rate_m_s=2.0),
    ],
)
print("\nMixed mission: 10 min hover, 20 min cruise, 1 min climb at 2 m/s:")
for seg in mission.segments:
    print(f"  {seg.kind:6s}: {seg.power_w:6.1f} W, {seg.energy_wh:6.1f} Wh")
print(f"Total: {mission.total_energy_wh:.1f} Wh over "
      f"{mission.total_distance_m / 1000.0:.1f} km, avg {mission.average_power_w:.1f} W")
