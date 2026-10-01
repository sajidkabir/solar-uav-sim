# solar-uav-sim

[![CI](https://github.com/sajidkabir/solar-uav-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/sajidkabir/solar-uav-sim/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A solar-powered UAV endurance simulator. It answers one question: **can this
aircraft sustain itself on sunlight alone, and if not, how much more solar
resource (or panel area) does it need?**

The simulator runs a 24-hour energy balance: solar power in against propulsion
and avionics power out, integrated through a battery model, and then solves for
the **charge-consumption parity point**, the exact irradiance multiplier at
which the day breaks even.

## Physics

- **Sun:** solar declination (Cooper), hour angle, and altitude; clear-sky
  global horizontal irradiance from the solar constant with bulk atmospheric
  transmittance by relative air mass.
- **Panel:** `P = G * A * eta * eta_mppt`, with panel area, cell efficiency,
  and MPPT losses.
- **Battery:** capacity with charge/discharge efficiencies and a
  depth-of-discharge floor.
- **Propulsion:** multirotor hover power from actuator-disk momentum theory,
  `P = T^1.5 / sqrt(2 * rho * A)`, corrected by figure of merit, plus climb
  power and an avionics base load. Air density from the ISA troposphere model.
- **Parity solver:** bisection on an irradiance scale factor until daily net
  energy crosses zero.

## Install

```bash
pip install -e .
```

Requires Python 3.10+, numpy, matplotlib.

## Usage

```bash
# 24-hour energy balance for Dhaka (default) on day 172
solar-uav-sim simulate

# Another site and date: latitude 51.5 (London), day 80 (equinox)
solar-uav-sim --lat 51.5 --day 80 simulate

# How much more sun (or panel) is needed to break even?
solar-uav-sim parity

# Save power and battery plots
solar-uav-sim plot --output day.png
```

Sample output (defaults: 1 m^2 of 22% panels, 500 Wh battery, 3 kg quad):

```
Energy in:     1567.3 Wh
Energy out:    6612.8 Wh
Net:          -5045.5 Wh
Min SoC:        100.0 Wh
End SoC:        100.0 Wh
```

The negative net is the honest answer for a heavy quad: multirotor solar
flight needs either a much lighter airframe or far more panel area, which is
exactly what the `parity` command quantifies.

```python
from solar_uav_sim import MissionConfig, PanelSpec, BatterySpec, MultirotorSpec, run_day

config = MissionConfig(latitude_deg=23.8, day_of_year=172)
panel = PanelSpec(area_m2=1.0, efficiency=0.22)
battery = BatterySpec(capacity_wh=500.0)
propulsion = MultirotorSpec(mass_kg=3.0, num_rotors=4, prop_diameter_m=0.33)

result = run_day(config, panel, battery, propulsion)
print(result.net_energy_wh)
```

## Validation

- Solar altitude at the equator on the equinox at solar noon is ~90 degrees;
  midnight irradiance is exactly zero.
- Panel output is linear in irradiance, area, and efficiency by construction.
- A 2 kg quad on 10-inch props draws ~180 W in hover, consistent with
  textbook momentum-theory examples.
- The parity solver brackets break-even: net energy at the solved factor is
  within 2% of total daily load.

## Roadmap

- Forward-flight power model (parasite + induced drag in cruise)
- Tilted and sun-tracking panel geometry
- Real weather derating (cloud cover from historical data)
- Fixed-wing airframe model

## License

MIT. See [LICENSE](LICENSE).
