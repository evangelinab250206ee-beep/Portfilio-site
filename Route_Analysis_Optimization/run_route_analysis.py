"""Command-line entry point for Phase 4 multi-route analysis."""
from __future__ import annotations

import argparse
from pathlib import Path

from route_optimizer import RouteOptimizer, VehicleConfig


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Find the best GPX route for a solar-assisted EV.")
    parser.add_argument("--routes-dir", default=str(project_root / "Route_dataset" / "kochi to bangalore"))
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--departure-date", default="2026-06-25")
    parser.add_argument("--departure-time", default="08:00")
    parser.add_argument("--speed-kmh", type=float, default=55.0)
    parser.add_argument("--vehicle-mass-kg", type=float, default=1500.0)
    parser.add_argument("--battery-capacity-kwh", type=float, default=60.0)
    parser.add_argument("--no-elevation-api", action="store_true")
    args = parser.parse_args()
    vehicle = VehicleConfig(vehicle_mass_kg=args.vehicle_mass_kg, battery_capacity_kwh=args.battery_capacity_kwh)
    optimizer = RouteOptimizer(args.departure_date, args.departure_time, args.speed_kmh, vehicle, not args.no_elevation_api)
    comparison = optimizer.process_routes(args.routes_dir, args.output_dir)
    print(comparison[["route", "route_score", "final_battery_remaining_percent", "total_solar_energy_kwh"]].to_string(index=False))
    print(f"\nBest route: {comparison.iloc[0]['route']}")


if __name__ == "__main__":
    main()
