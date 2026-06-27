"""Run the Weather Prediction CSV → Solar EV Energy output pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from solar_ev_predictor import load_weather_predictions, predict_trip_solar_energy, save_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert weather_predictions.csv into EV roof-solar energy results."
    )
    parser.add_argument(
        "csv_file", nargs="?", default="weather_predictions.csv",
        help="Weather Prediction System CSV (default: weather_predictions.csv)",
    )
    parser.add_argument("--output-dir", default="output", help="Folder for CSV, report, and PNG charts")
    parser.add_argument(
        "--vehicle-speed-kmh", type=float, default=None,
        help="Use this speed for every point when the input CSV has no route speed column.",
    )
    parser.add_argument(
        "--trip-energy-demand-kwh", type=float, default=None,
        help="Optional external trip-energy demand for solar contribution percentage only.",
    )
    args = parser.parse_args()

    weather_points = load_weather_predictions(args.csv_file)
    if args.vehicle_speed_kmh is not None:
        if args.vehicle_speed_kmh < 0:
            parser.error("--vehicle-speed-kmh must be zero or greater.")
        weather_points["vehicle_speed_kmh"] = args.vehicle_speed_kmh
    elif (weather_points["vehicle_speed_kmh"] == 0).all():
        print("Warning: no vehicle speed supplied; distance will be reported as 0 km.")

    results, summary = predict_trip_solar_energy(
        weather_points, trip_energy_demand_kwh=args.trip_energy_demand_kwh,
    )
    saved = save_results(results, summary, Path(args.output_dir))
    print(f"Processed {len(results):,} route point(s).")
    print(f"Total solar energy: {summary['total_trip_solar_energy_wh']} Wh ({summary['total_trip_solar_energy_kwh']} kWh)")
    print("Created files:")
    for name, path in saved.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
