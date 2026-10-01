from solar_uav_sim import Battery, BatterySpec


def test_charge_round_trip_efficiency():
    spec = BatterySpec(capacity_wh=1000.0, charge_efficiency=0.95, discharge_efficiency=0.97)
    battery = Battery(spec, initial_soc_wh=500.0)
    stored = battery.charge(100.0, 1.0)
    assert stored == 95.0
    assert battery.soc_wh == 595.0
    delivered = battery.discharge(100.0, 1.0)
    assert abs(delivered - 100.0) < 1e-9
    assert abs(battery.soc_wh - (595.0 - 100.0 / 0.97)) < 1e-9


def test_charge_is_capped_at_capacity():
    spec = BatterySpec(capacity_wh=100.0)
    battery = Battery(spec, initial_soc_wh=99.0)
    stored = battery.charge(100.0, 1.0)
    assert stored == 1.0
    assert battery.soc_wh == 100.0


def test_discharge_respects_depth_of_discharge():
    spec = BatterySpec(capacity_wh=100.0, max_depth_of_discharge=0.8)
    battery = Battery(spec, initial_soc_wh=100.0)
    delivered = battery.discharge(1000.0, 1.0)
    # floor at 20% of capacity; 80 Wh stored, delivered at 0.97 efficiency
    assert battery.soc_wh == 20.0
    assert abs(delivered - 80.0 * 0.97) < 1e-6
