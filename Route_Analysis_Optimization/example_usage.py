"""Example Phase 4 run using the three GPX routes in this project."""
from pathlib import Path

from route_optimizer import RouteOptimizer

project_root = Path(__file__).resolve().parents[1]
routes = project_root / "Route_dataset" / "kochi to bangalore"
optimizer = RouteOptimizer(
    departure_date="2026-06-25",
    departure_time="08:00",
    travel_speed_kmh=55,
)
comparison = optimizer.process_routes(routes, "output")
print(comparison[["route", "route_score", "final_battery_remaining_percent"]].to_string(index=False))
