# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions follow
[Semantic Versioning](https://semver.org/).

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
