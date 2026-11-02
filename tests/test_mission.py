import argparse

import pytest

from solar_uav_sim import (
    MultirotorSpec,
    Segment,
    air_density_kg_m3,
    climb_power_w,
    forward_power_w,
    hover_power_w,
    run_mission,
    segment_from_dict,
    segment_power_w,
)
from solar_uav_sim.cli import cmd_cruise, cmd_mission, cmd_power_curve


def _spec():
    return MultirotorSpec(mass_kg=3.0, num_rotors=4, prop_diameter_m=0.33)


def test_segment_powers_use_the_right_models():
    spec = _spec()
    rho = air_density_kg_m3(0.0)
    assert segment_power_w(spec, rho, Segment("hover", 60.0)) == hover_power_w(spec, rho)
    assert segment_power_w(spec, rho, Segment("cruise", 60.0, speed_m_s=12.0)) == forward_power_w(
        spec, rho, 12.0
    )
    assert segment_power_w(spec, rho, Segment("climb", 60.0, climb_rate_m_s=2.0)) == climb_power_w(
        spec, rho, 2.0
    )


def test_mission_totals_and_cruise_saves_energy():
    spec = _spec()
    rho = air_density_kg_m3(0.0)
    mission = run_mission(
        spec,
        rho,
        [
            Segment("hover", 600.0),
            Segment("cruise", 1200.0, speed_m_s=15.0),
            Segment("climb", 60.0, climb_rate_m_s=2.0),
        ],
    )
    assert mission.total_time_s == 1860.0
    assert mission.total_distance_m == 15.0 * 1200.0
    assert mission.total_energy_wh == pytest.approx(
        sum(seg.power_w * seg.duration_s / 3600.0 for seg in mission.segments)
    )
    assert mission.average_power_w == pytest.approx(mission.total_energy_wh * 3600.0 / 1860.0)
    # Cruise segment draws less power than the hover segment.
    assert mission.segments[1].power_w < mission.segments[0].power_w
    # Climb segment draws more than hover for the same aircraft.
    assert mission.segments[2].power_w > mission.segments[0].power_w
    assert mission.segments[2].vertical_m == 120.0


def test_mission_validation():
    spec = _spec()
    rho = air_density_kg_m3(0.0)
    with pytest.raises(ValueError):
        run_mission(spec, rho, [])
    with pytest.raises(ValueError):
        run_mission(spec, rho, [Segment("hover", 0.0)])
    with pytest.raises(ValueError):
        run_mission(spec, rho, [Segment("loiter", 60.0)])
    with pytest.raises(ValueError):
        run_mission(spec, rho, [Segment("cruise", 60.0, speed_m_s=-3.0)])
    with pytest.raises(ValueError):
        run_mission(spec, rho, [Segment("climb", 60.0, climb_rate_m_s=-1.0)])


def test_segment_from_dict():
    seg = segment_from_dict({"kind": "cruise", "duration_s": 300, "speed_m_s": 12})
    assert seg == Segment("cruise", 300.0, speed_m_s=12.0)
    assert segment_from_dict({"kind": "hover", "duration_s": 60}).speed_m_s == 0.0


def test_cli_cruise_and_power_curve(capsys):
    args = argparse.Namespace(altitude=100.0, speed=12.0)
    assert cmd_cruise(args) == 0
    out = capsys.readouterr().out
    assert "Total:" in out and "Parasite:" in out
    args = argparse.Namespace(altitude=100.0, max_speed=10.0, step=5.0)
    assert cmd_power_curve(args) == 0
    out = capsys.readouterr().out
    assert "Minimum-power cruise:" in out


def test_cli_mission_file(tmp_path, capsys):
    path = tmp_path / "mission.json"
    path.write_text(
        '[{"kind": "hover", "duration_s": 600}, '
        '{"kind": "cruise", "duration_s": 1200, "speed_m_s": 15.0}]'
    )
    args = argparse.Namespace(altitude=100.0, segments=str(path))
    assert cmd_mission(args) == 0
    out = capsys.readouterr().out
    assert "Total:" in out and "Share of 500 Wh battery:" in out
