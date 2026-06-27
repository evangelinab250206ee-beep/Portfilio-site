"""Run Phase 3: solar_ev_results.csv -> EV energy and battery outputs."""
import argparse

from ev_energy_predictor import VehicleConfig, load_solar_results, predict_trip_energy, save_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Create per-point EV energy and battery predictions.")
    parser.add_argument("solar_csv", nargs="?", default="../Solar_EV_Energy/output/solar_ev_results.csv")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--vehicle-mass-kg", type=float, default=1500)
    parser.add_argument("--battery-capacity-kwh", type=float, default=60)
    parser.add_argument("--initial-battery-percent", type=float, default=100)
    args = parser.parse_args()

    vehicle = VehicleConfig(
        vehicle_mass_kg=args.vehicle_mass_kg,
        battery_capacity_kwh=args.battery_capacity_kwh,
        initial_battery_percent=args.initial_battery_percent,
    )
    route_points = load_solar_results(args.solar_csv)
    results, summary = predict_trip_energy(route_points, vehicle)
    saved = save_results(results, summary, args.output_dir)
    print(f"Processed {summary['route_points']:,} route point(s).")
    print(f"Energy consumed: {summary['energy_consumed_kwh']} kWh")
    print(f"Battery remaining: {summary['battery_remaining_percent']}%")
    print(f"Estimated remaining range: {summary['remaining_range_km']} km")
    print("Saved:")
    for name, path in saved.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
