from solar_uav_sim import (
    MultirotorSpec,
    air_density_kg_m3,
    hover_power_w,
    panel_power_w,
)
from solar_uav_sim.panel import PanelSpec


def test_panel_power_scales_with_area_and_efficiency():
    panel = PanelSpec(area_m2=1.0, efficiency=0.20, mppt_efficiency=1.0)
    assert panel_power_w(panel, 1000.0) == 200.0
    assert panel_power_w(panel, 0.0) == 0.0


def test_hover_power_in_plausible_band():
    # 2 kg quad, 10-inch props: with the calibrated drivetrain efficiency
    # (2026-10-09), momentum theory gives about 276 W electrical.
    spec = MultirotorSpec(mass_kg=2.0, num_rotors=4, prop_diameter_m=0.254, figure_of_merit=0.7)
    power = hover_power_w(spec, air_density_kg_m3(0.0))
    assert 240.0 < power < 330.0


def test_heavier_aircraft_needs_more_power():
    light = MultirotorSpec(mass_kg=2.0, num_rotors=4, prop_diameter_m=0.254)
    heavy = MultirotorSpec(mass_kg=4.0, num_rotors=4, prop_diameter_m=0.254)
    rho = air_density_kg_m3(0.0)
    assert hover_power_w(heavy, rho) > hover_power_w(light, rho)


def test_thinner_air_needs_more_power():
    spec = MultirotorSpec(mass_kg=2.0, num_rotors=4, prop_diameter_m=0.254)
    assert hover_power_w(spec, air_density_kg_m3(3000.0)) > hover_power_w(spec, air_density_kg_m3(0.0))
