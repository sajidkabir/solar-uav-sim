# solar-uav-sim

[![CI](https://github.com/sajidkabir/solar-uav-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/sajidkabir/solar-uav-sim/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23077717.svg)](https://doi.org/10.5281/zenodo.23077717)

A solar-powered UAV endurance simulator. It models the full 24-hour energy
balance of a solar-electric multirotor: sunlight in, propulsion and avionics
out, and a battery in between. On top of the simulator sits a
**charge-consumption parity solver** that answers the design question behind
solar flight: how much sunlight (or panel, or daylight) would this aircraft
need for energy in to equal energy out over a full day?

The simulator grew out of undergraduate thesis work on a solar-powered
quadcopter. It is built to be read, extended, and argued with: small modules,
explicit physics, honest limitations, and tests that check the numbers
against first principles.

## Features

- **Solar geometry and clear-sky irradiance**: declination (Cooper), hour
  angle, solar altitude, air-mass transmittance, daylight duration for any
  latitude and day of year.
- **Panel model**: area, cell efficiency, and MPPT efficiency, producing
  instantaneous electrical power from irradiance and sun angle.
- **Battery model**: capacity, charge and discharge efficiency, and a maximum
  depth-of-discharge floor. State of charge is integrated step by step and
  never silently goes negative or overfull.
- **Propulsion model**: hover power from actuator-disk momentum theory with
  a rotor figure of merit and a motor/controller drivetrain efficiency
  (calibrated against the DJI Mavic 3 spec point), ISA air density at
  altitude, plus a climb-power term.
- **Forward-flight model**: induced power that falls with speed (Glauert),
  profile power growing with advance ratio, and parasite drag growing
  with V^3, giving the classic U-shaped power curve and a
  minimum-power cruise speed. Forward power at zero speed is exactly
  the hover power, so validated hover numbers are unchanged.
- **Mission pricing**: timed hover, cruise, and climb segments summed to
  total energy, distance, and average power, so a real mission can be
  priced instead of assuming an all-day hover.
- **Day simulation**: a configurable mission (latitude, day of year,
  altitude, panel, battery, aircraft) integrated over 24 hours, returning
  energy in, energy out, net balance, and the state-of-charge trace.
- **Parity solver**: bisection on an irradiance scale factor that finds the
  exact point where daily harvest equals daily consumption; the search
  bracket grows automatically if break-even lies beyond it.
- **CLI**: `simulate`, `parity`, `plot`, `cruise`, `power-curve`, and
  `mission` subcommands, plus a Python API for embedding the models in
  your own design studies.

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/sajidkabir/solar-uav-sim.git
cd solar-uav-sim
pip install -e .
```

For development (adds the test runner):

```bash
pip install -e . pytest
pytest -q
```

## Quickstart

### Command line

Simulate a 3 kg quadcopter with a 1 m2 panel over Dhaka on the summer
solstice:

```bash
solar-uav-sim simulate --lat 23.8 --day 172 --panel-area 1.0 --battery-wh 500 --mass-kg 3.0
```

```text
Energy in:     1567.3 Wh
Energy out:   11924.7 Wh
Net:         -10357.4 Wh
Min SoC:        100.0 Wh
End SoC:        100.0 Wh
```

Ask what it would take to break even:

```bash
solar-uav-sim parity --lat 23.8 --day 172 --panel-area 1.0 --battery-wh 500 --mass-kg 3.0
```

Plot the state-of-charge curve to a PNG:

```bash
solar-uav-sim plot --output soc.png
```

Price forward flight and a mixed mission:

```bash
solar-uav-sim cruise --speed 15
solar-uav-sim power-curve --max-speed 30 --step 5
solar-uav-sim mission --segments examples/mission.json
```

### Python API

```python
from solar_uav_sim import (
    BatterySpec, MissionConfig, MultirotorSpec, PanelSpec,
    parity_scale_factor, simulate_day,
)

config = MissionConfig(
    latitude_deg=23.81,
    day_of_year=172,
    altitude_m=100.0,
    panel=PanelSpec(area_m2=1.0, efficiency=0.22),
    battery=BatterySpec(capacity_wh=500.0),
    aircraft=MultirotorSpec(mass_kg=3.0, rotor_diameter_m=0.33, num_rotors=4),
)

result = simulate_day(config)
print(result.energy_in_wh, result.energy_out_wh, result.net_wh)
print("Parity factor:", parity_scale_factor(config))
```

## How it works

| Module | Responsibility |
| --- | --- |
| `sun.py` | Solar position and clear-sky irradiance |
| `atmosphere.py` | ISA troposphere density |
| `panel.py` | Photovoltaic power from irradiance |
| `battery.py` | Charge/discharge bookkeeping with efficiency and DoD limits |
| `propulsion.py` | Hover, climb, and forward-flight power from momentum theory |
| `mission.py` | Segment-based mission energy (hover, cruise, climb) |
| `simulation.py` | The 24-hour integration loop and the parity solver |
| `cli.py` | Command-line interface |

Key relations:

- Solar declination (Cooper): delta = 23.45 deg * sin(360 * (284 + N) / 365)
- Hover induced velocity: v_i = sqrt(T / (2 * rho * A))
- Hover power: P = T * v_i / (figure_of_merit * drivetrain_efficiency),
  with T = m * g for the full rotor system; defaults calibrated so the
  DJI Mavic 3 spec point (0.895 kg, 40 min hover, 77 Wh) reproduces 115.5 W
- Forward induced velocity (Glauert): v_i = v_h^2 / sqrt(V^2 + v_i^2)
- Forward power: induced (falling with V) + profile increment
  (proportional to 3 mu^2 above hover, mu = V / tip speed) + parasite
  (0.5 * rho * CdA * V^3 / drivetrain_efficiency) + avionics
- Daily balance: net = harvested solar energy - propulsion energy over 24 h,
  with the battery absorbing surpluses and covering deficits down to its
  depth-of-discharge floor

## Validation and sanity checks

The test suite (28 tests) checks the physics, not just the plumbing:

- Solar altitude peaks at local noon; irradiance is zero at night.
- On the solstice, daylight exceeds 13 hours at latitude 23.8.
- A battery can never discharge below its depth-of-discharge floor.
- Hover power matches a hand-computed momentum-theory value within 2 percent.
- A light platform (0.5 kg, 2 m2 of panel) ends the day energy-positive,
  while a heavy quad on a small panel does not, and the parity solver
  brackets the break-even point between them.
- Forward power at zero speed equals hover power exactly; induced
  velocity falls with speed toward the v_h^2 / V asymptote; the power
  curve is U-shaped (cruise cheaper than hover, then drag-dominated);
  a mixed hover/cruise/climb mission prices to its segment sum.

## Honest limitations

- Clear-sky irradiance only: no clouds, haze, or panel soiling yet.
- The 24-hour day simulation still assumes a hover load; mixed
  hover/cruise/climb flights are priced with the mission tool, not
  inside the day loop. No wind model yet.
- Forward-flight drag area, tip speed, solidity, and profile drag
  defaults are typical small-quad estimates, not calibrated to a
  specific airframe.
- Panels are assumed horizontal and fixed to the airframe.
- The battery model has no C-rate or thermal limits.

These are deliberate. Each one is a clean extension point, listed below.

## Roadmap and room for exploration

Ideas are welcome. Roughly in order of expected value:

- **Mission profiles in the day loop**: timed segments inside the 24-hour
  simulation instead of a single all-day hover (segment pricing exists
  as a standalone tool since v1.1.0).
- **Weather derating**: cloud cover factors and measured irradiance data
  (for example from NASA POWER) in place of the clear-sky model.
- **Tilted and tracking panels**: panel normal vector vs sun vector.
- **Fixed-wing model**: lift-to-drag based cruise power for comparison with
  the multirotor case.
- **Design sweeps and optimization**: grid search or gradient-free
  optimization over panel area, battery size, and mass to map the feasible
  design space around parity.
- **Battery realism**: C-rate limits, Peukert effect, temperature derating.
- **A small web or GUI front end** for classroom use.

If you build one of these, open an issue or a pull request. Design notes in
the PR description are appreciated: what assumption changed, and what it did
to the parity point.

## Project structure

```text
src/solar_uav_sim/   the package (sun, atmosphere, panel, battery,
                     propulsion, simulation, cli)
tests/               pytest suite, physics sanity checks included
examples/            runnable example missions
.github/workflows/   CI: install and run the test suite on every push
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: fork, branch,
test, pull request. Every change should keep `pytest -q` green and should
not move the validated numbers without explaining why in the PR.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Citation

If you use this project in research, please cite the archived release:

Sajid Kabir Saji (2026). solar-uav-sim (v1.0.1) [Software]. Zenodo. https://doi.org/10.5281/zenodo.23077718

The concept DOI https://doi.org/10.5281/zenodo.23077717 always resolves to the latest version.

## License

MIT. See [LICENSE](LICENSE).

## Author

Sajid Kabir Saji, aeronautical engineer. Research interests: onboard
autonomous decision-making for UAVs and solar-electric flight endurance.
More at [sajidkabir.com](https://sajidkabir.com).
