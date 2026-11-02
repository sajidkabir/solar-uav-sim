# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-11-02

### Added

- Forward-flight power model (`forward_power_w`, `forward_power_breakdown_w`,
  `forward_induced_velocity_m_s`): Glauert induced velocity that falls with
  speed, blade-element profile power growing with advance ratio
  (1 + 3 mu^2), and parasite power growing with V^3. The curve is
  U-shaped: a 3 kg quad cruises cheaper than it hovers up to a
  minimum-power speed, after which drag dominates.
- Minimum-power cruise speed (`best_cruise_speed_m_s`) by a 0.25 m/s scan.
- Segment-based mission pricing (`mission.py`): timed hover, cruise, and
  climb segments summed to total energy, distance, and average power,
  plus JSON segment lists (`segment_from_dict`).
- CLI subcommands: `cruise` (power breakdown at one speed), `power-curve`
  (power vs speed table with the minimum-power point), and `mission`
  (price a JSON segment file, with its share of the battery).
- Test suites for forward flight (7 tests) and missions (6 tests).

### Notes

- Forward power at zero speed is exactly the hover power, by
  construction: the hover model's figure of merit already absorbs profile
  power at hover, so the forward model adds only the profile increment
  above hover. Validated hover numbers are unchanged.
- The 24-hour day simulation still assumes a hover load; the mission
  tool is the place for mixed hover/cruise/climb flights.
- Forward-flight drag area, tip speed, solidity, and profile drag
  defaults are typical small-quad estimates, documented in the code, not
  calibrated to a specific airframe. Set them from measured data for a
  real aircraft before using cruise numbers for flight planning.
- This release also pushes two previously local-only 2026-10-09 changes
  to the remote for the first time: the drivetrain-efficiency hover
  calibration in propulsion.py (figure of merit 0.55, drivetrain 0.65,
  Mavic 3 spec point) and the parity solver's automatic bracket growth
  in simulation.py. The README quickstart numbers are corrected to the
  calibrated hover model (energy out 11924.7 Wh, not 6612.8 Wh).

## [1.0.0] - 2026-10-01

First stable release.

### Added

- 24-hour energy-balance day simulation (`simulate_day`) integrating solar
  harvest, panel output, battery state of charge, and propulsion load.
- Charge-consumption parity solver (`parity_scale_factor`) using bisection
  on an irradiance scale factor.
- Solar geometry and clear-sky irradiance model (Cooper declination, hour
  angle, air-mass transmittance).
- ISA troposphere air density.
- Panel model with cell and MPPT efficiency.
- Battery model with charge/discharge efficiency and depth-of-discharge
  floor.
- Multirotor hover and climb power from actuator-disk momentum theory.
- Command-line interface with `simulate`, `parity`, and `plot`
  subcommands.
- Test suite of 15 tests covering the physics sanity checks, plus GitHub
  Actions CI on Python 3.12.
- Example mission: 3 kg quadcopter over Dhaka on the summer solstice.

### Fixed

- Energy accounting in the day simulation: harvested solar energy is now
  counted in full, not only the surplus left after serving the load.
