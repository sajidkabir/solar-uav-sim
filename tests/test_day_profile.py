"""Tests for timed mission profiles inside the 24-hour day loop."""

import json

import pytest

from solar_uav_sim import (
    BatterySpec,
    DayProfile,
    MissionConfig,
    MultirotorSpec,
    PanelSpec,
    TimedSegment,
    parity_scale_factor,
    profile_from_dicts,
    run_day,
)
from solar_uav_sim.mission import Segment
from solar_uav_sim.profile import DAY_HOURS


def _specs(panel_area=1.0, mass_kg=3.0):
    panel = PanelSpec(area_m2=panel_area, efficiency=0.22)
    battery = BatterySpec(capacity_wh=500.0)
    propulsion = MultirotorSpec(mass_kg=mass_kg, num_rotors=4, prop_diameter_m=0.33)
    return panel, battery, propulsion


def _config():
    return MissionConfig(latitude_deg=23.8, day_of_year=172)


def _morning_sortie():
    return DayProfile(
        (
            TimedSegment(
                start_hour=6.0,
                segment=Segment(kind="cruise", duration_s=3600.0, speed_m_s=12.0),
            ),
        )
    )


def test_no_profile_is_all_day_hover():
    # Regression guard: the default day is unchanged by the feature.
    config = _config()
    panel, battery, propulsion = _specs()
    result = run_day(config, panel, battery, propulsion)
    assert result.flight_time_s == pytest.approx(24 * 3600)
    assert result.flight_distance_m == 0.0
    assert set(result.load_kind) == {"hover"}
    assert result.energy_out_wh == pytest.approx(11883.4, rel=0.01)


def test_profile_reduces_energy_out():
    config = _config()
    panel, battery, propulsion = _specs()
    hover_day = run_day(config, panel, battery, propulsion)
    profile_day = run_day(config, panel, battery, propulsion, profile=_morning_sortie())
    assert profile_day.energy_out_wh < hover_day.energy_out_wh
    assert profile_day.energy_in_wh == hover_day.energy_in_wh
    assert profile_day.net_energy_wh > hover_day.net_energy_wh


def test_flight_time_and_distance_accumulate():
    config = _config()
    panel, battery, propulsion = _specs()
    result = run_day(config, panel, battery, propulsion, profile=_morning_sortie())
    assert result.flight_time_s == pytest.approx(3600.0)
    assert result.flight_distance_m == pytest.approx(12.0 * 3600.0)
    assert result.load_kind[72] == "cruise"  # step at hour 6.0 (5-minute steps)
    assert result.load_kind[0] == "ground"
    assert result.load_kind[-1] == "ground"


def test_ground_load_is_zero():
    config = _config()
    panel, battery, propulsion = _specs()
    result = run_day(config, panel, battery, propulsion, profile=_morning_sortie())
    assert result.load_power[0] == 0.0
    assert result.load_power[72] > 0.0


def test_midday_charging_recovers_battery():
    # A morning sortie drains the battery; sitting on the ground at
    # midday lets the sun put energy back, so the profile day ends
    # with more charge than the all-hover day (which ends on the floor).
    config = _config()
    panel, battery, propulsion = _specs()
    hover_day = run_day(config, panel, battery, propulsion)
    profile_day = run_day(config, panel, battery, propulsion, profile=_morning_sortie())
    assert profile_day.end_soc_wh > hover_day.end_soc_wh
    # The sortie only dips the battery part-way; the all-hover day
    # grinds it down to the depth-of-discharge floor.
    assert profile_day.min_soc_wh > hover_day.min_soc_wh


def test_empty_profile_draws_nothing():
    config = _config()
    panel, battery, propulsion = _specs()
    result = run_day(config, panel, battery, propulsion, profile=DayProfile(()))
    assert result.energy_out_wh == 0.0
    assert result.flight_time_s == 0.0
    assert set(result.load_kind) == {"ground"}
    assert result.end_soc_wh == 500.0


def test_overlapping_segments_rejected():
    with pytest.raises(ValueError, match="overlap"):
        DayProfile(
            (
                TimedSegment(6.0, Segment(kind="hover", duration_s=3600.0)),
                TimedSegment(6.5, Segment(kind="hover", duration_s=3600.0)),
            )
        )


def test_segment_ending_after_midnight_rejected():
    with pytest.raises(ValueError, match="after hour 24"):
        DayProfile((TimedSegment(23.5, Segment(kind="hover", duration_s=3600.0)),))


def test_segment_start_out_of_range_rejected():
    with pytest.raises(ValueError, match=r"\[0, 24\)"):
        DayProfile((TimedSegment(-1.0, Segment(kind="hover", duration_s=60.0)),))
    with pytest.raises(ValueError, match=r"\[0, 24\)"):
        DayProfile((TimedSegment(24.0, Segment(kind="hover", duration_s=60.0)),))


def test_segment_ending_exactly_at_midnight_allowed():
    profile = DayProfile((TimedSegment(23.0, Segment(kind="hover", duration_s=3600.0)),))
    assert profile.segments[0].end_hour == DAY_HOURS


def test_touching_segments_allowed_and_unsorted_input_sorted():
    profile = DayProfile(
        (
            TimedSegment(7.0, Segment(kind="hover", duration_s=3600.0)),
            TimedSegment(6.0, Segment(kind="hover", duration_s=3600.0)),
        )
    )
    assert [item.start_hour for item in profile.segments] == [6.0, 7.0]


def test_profile_from_dicts_round_trip():
    data = [
        {"start_hour": 6.0, "kind": "cruise", "duration_s": 3600, "speed_m_s": 12.0},
        {"start_hour": 12.0, "kind": "hover", "duration_s": 600},
        {"start_hour": 16.0, "kind": "climb", "duration_s": 120, "climb_rate_m_s": 2.0},
    ]
    profile = profile_from_dicts(data)
    assert len(profile.segments) == 3
    assert profile.segments[2].segment.kind == "climb"
    assert profile.segments[2].segment.climb_rate_m_s == 2.0


def test_profile_from_dicts_rejects_unknown_kind_and_non_list():
    with pytest.raises(ValueError, match="unknown segment kind"):
        profile_from_dicts([{"start_hour": 6.0, "kind": "orbit", "duration_s": 60}])
    with pytest.raises(ValueError, match="JSON list"):
        profile_from_dicts({"start_hour": 6.0})


def test_parity_with_profile_is_lower_than_all_day_hover():
    config = _config()
    panel, battery, propulsion = _specs(panel_area=1.0, mass_kg=1.5)
    hover_parity = parity_scale_factor(config, panel, battery, propulsion)
    profile_parity = parity_scale_factor(
        config, panel, battery, propulsion, profile=_morning_sortie()
    )
    assert profile_parity < hover_parity
    # The profile day really breaks even at its own factor.
    net = run_day(config, panel, battery, propulsion, profile_parity, _morning_sortie()).net_energy_wh
    out = run_day(config, panel, battery, propulsion, profile_parity, _morning_sortie()).energy_out_wh
    assert abs(net) < 0.02 * out


def test_climb_segment_prices_climb_power_in_day_loop():
    from solar_uav_sim import climb_power_w
    from solar_uav_sim.atmosphere import air_density_kg_m3

    config = _config()
    panel, battery, propulsion = _specs()
    profile = DayProfile(
        (TimedSegment(10.0, Segment(kind="climb", duration_s=300.0, climb_rate_m_s=2.0)),)
    )
    result = run_day(config, panel, battery, propulsion, profile=profile)
    rho = air_density_kg_m3(100.0)
    assert result.load_power[120] == pytest.approx(climb_power_w(propulsion, rho, 2.0))
    assert result.flight_time_s == pytest.approx(300.0)
    assert result.flight_distance_m == 0.0


def test_cli_simulate_with_profile(tmp_path, capsys):
    from solar_uav_sim.cli import main

    data = [
        {"start_hour": 6.0, "kind": "cruise", "duration_s": 3600, "speed_m_s": 12.0},
    ]
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    import sys

    sys.argv = ["solar-uav-sim", "simulate", "--profile", str(path)]
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Flight time:" in out
    assert "Distance:" in out


def test_cli_profile_missing_file_exits_nonzero(tmp_path):
    from solar_uav_sim.cli import main

    import sys

    sys.argv = ["solar-uav-sim", "simulate", "--profile", str(tmp_path / "nope.json")]
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code != 0
