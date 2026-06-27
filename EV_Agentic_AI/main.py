"""Command-line entry point for EV Agentic AI."""

from __future__ import annotations

import argparse
from datetime import datetime

from agents.decision_agent import DecisionAgent
from config.settings import settings
from utils.types import Location


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EV Agentic AI route and energy assistant")
    parser.add_argument("--start-lat", type=float, default=settings.default_latitude)
    parser.add_argument("--start-lon", type=float, default=settings.default_longitude)
    parser.add_argument("--dest-lat", type=float, default=settings.default_latitude + 0.08)
    parser.add_argument("--dest-lon", type=float, default=settings.default_longitude + 0.12)
    parser.add_argument("--soc", type=float, default=settings.default_soc)
    parser.add_argument("--speed", type=float, default=55.0)
    parser.add_argument("--gradient", type=float, default=1.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = DecisionAgent().decide(
        start=Location(args.start_lat, args.start_lon, "start"),
        destination=Location(args.dest_lat, args.dest_lon, "destination"),
        current_soc_pct=args.soc,
        vehicle_speed_kmh=args.speed,
        road_gradient_pct=args.gradient,
        when=datetime.now(),
    )
    print("EV Agentic AI Decision")
    print(f"Route distance: {summary.route.distance_km:.1f} km")
    print(f"Estimated travel time: {summary.route.travel_time_min:.0f} min")
    print(f"Energy required: {summary.route.energy_required_kwh:.2f} kWh")
    print(f"Remaining range: {summary.energy.remaining_range_km:.1f} km")
    print(f"Estimated battery remaining: {summary.estimated_battery_remaining_pct:.1f}%")
    print(f"Weather risk: {summary.weather_risk}")
    print(f"Charging: {summary.charging.message}")


if __name__ == "__main__":
    main()
