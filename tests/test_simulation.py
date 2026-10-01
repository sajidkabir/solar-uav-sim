from solar_uav_sim import (
    BatterySpec,
    MissionConfig,
    MultirotorSpec,
    PanelSpec,
    parity_scale_factor,
    run_day,
)


def _specs(panel_area=1.0, mass_kg=3.0):
    panel = PanelSpec(area_m2=panel_area, efficiency=0.22)
    battery = BatterySpec(capacity_wh=500.0)
    propulsion = MultirotorSpec(mass_kg=mass_kg, num_rotors=4, prop_diameter_m=0.33)
    return panel, battery, propulsion


def test_net_energy_grows_with_panel_area():
    # More panel always helps, even when break-even is out of reach.
    config = MissionConfig(latitude_deg=23.8, day_of_year=172)
    small = run_day(config, *_specs(panel_area=0.5))
    big = run_day(config, *_specs(panel_area=2.0))
    assert big.net_energy_wh > small.net_energy_wh


def test_light_aircraft_can_break_even():
    # A 0.5 kg platform sips power; 2 m^2 of panels cover it on a clear day.
    config = MissionConfig(latitude_deg=23.8, day_of_year=172)
    panel, battery, propulsion = _specs(panel_area=2.0, mass_kg=0.5)
    result = run_day(config, panel, battery, propulsion)
    assert result.net_energy_wh > 0.0


def test_tiny_panel_gives_negative_net_energy():
    config = MissionConfig(latitude_deg=23.8, day_of_year=172)
    panel, battery, propulsion = _specs(panel_area=0.05)
    result = run_day(config, panel, battery, propulsion)
    assert result.net_energy_wh < 0.0


def test_parity_factor_brackets_break_even():
    # 1.5 kg aircraft: break-even sits inside the [0, 3] search bracket.
    config = MissionConfig(latitude_deg=23.8, day_of_year=172)
    panel, battery, propulsion = _specs(panel_area=1.0, mass_kg=1.5)
    factor = parity_scale_factor(config, panel, battery, propulsion)
    assert 0.0 < factor < 3.0
    net = run_day(config, panel, battery, propulsion, factor).net_energy_wh
    out = run_day(config, panel, battery, propulsion, factor).energy_out_wh
    assert abs(net) < 0.02 * out
