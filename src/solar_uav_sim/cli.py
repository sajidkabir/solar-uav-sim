"""Command-line interface for solar-uav-sim."""

from __future__ import annotations

import argparse
import json

from .battery import BatterySpec
from .panel import PanelSpec
from .propulsion import MultirotorSpec
from .simulation import MissionConfig, parity_scale_factor, run_day


def _default_specs():
    panel = PanelSpec(area_m2=1.0, efficiency=0.22)
    battery = BatterySpec(capacity_wh=500.0)
    propulsion = MultirotorSpec(mass_kg=3.0, num_rotors=4, prop_diameter_m=0.33)
    return panel, battery, propulsion


def cmd_simulate(args: argparse.Namespace) -> int:
    config = MissionConfig(latitude_deg=args.lat, day_of_year=args.day, altitude_m=args.altitude)
    panel, battery, propulsion = _default_specs()
    result = run_day(config, panel, battery, propulsion)
    print(f"Energy in:   {result.energy_in_wh:8.1f} Wh")
    print(f"Energy out:  {result.energy_out_wh:8.1f} Wh")
    print(f"Net:         {result.net_energy_wh:8.1f} Wh")
    print(f"Min SoC:     {result.min_soc_wh:8.1f} Wh")
    print(f"End SoC:     {result.end_soc_wh:8.1f} Wh")
    return 0


def cmd_parity(args: argparse.Namespace) -> int:
    config = MissionConfig(latitude_deg=args.lat, day_of_year=args.day, altitude_m=args.altitude)
    panel, battery, propulsion = _default_specs()
    factor = parity_scale_factor(config, panel, battery, propulsion)
    print(f"Parity irradiance factor: {factor:.3f}")
    if factor <= 1.0:
        print("The configuration sustains itself on a clear-sky day at this site.")
    else:
        print(f"Needs {100.0 * (factor - 1.0):.1f}% more solar resource (or panel area) to break even.")
    return 0


def cmd_plot(args: argparse.Namespace) -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    config = MissionConfig(latitude_deg=args.lat, day_of_year=args.day, altitude_m=args.altitude)
    panel, battery, propulsion = _default_specs()
    result = run_day(config, panel, battery, propulsion)

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    axes[0].plot(result.hours, result.solar_power, label="Solar power (W)")
    axes[0].plot(result.hours, result.load_power, label="Load power (W)")
    axes[0].set_ylabel("Power (W)")
    axes[0].legend()
    axes[1].plot(result.hours, result.soc, label="Battery SoC (Wh)", color="green")
    axes[1].set_ylabel("Energy (Wh)")
    axes[1].set_xlabel("Hour of day")
    axes[1].legend()
    fig.suptitle(f"Solar UAV day simulation: lat {args.lat}, day {args.day}")
    fig.tight_layout()
    fig.savefig(args.output)
    print(f"Saved {args.output}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="solar-uav-sim", description="Solar-powered UAV endurance simulator")
    parser.add_argument("--lat", type=float, default=23.8, help="Latitude in degrees (default: Dhaka)")
    parser.add_argument("--day", type=int, default=172, help="Day of year 1-365 (default: 172)")
    parser.add_argument("--altitude", type=float, default=100.0, help="Flight altitude in meters")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("simulate", help="Run a 24-hour energy-balance simulation")
    sub.add_parser("parity", help="Find the irradiance factor needed to break even")
    plot = sub.add_parser("plot", help="Save power and battery plots to a PNG file")
    plot.add_argument("--output", default="day.png")

    args = parser.parse_args()
    if args.command == "simulate":
        raise SystemExit(cmd_simulate(args))
    if args.command == "parity":
        raise SystemExit(cmd_parity(args))
    if args.command == "plot":
        raise SystemExit(cmd_plot(args))


if __name__ == "__main__":
    main()
