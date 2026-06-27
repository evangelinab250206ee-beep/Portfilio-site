"""Geospatial helpers with no mandatory online dependency."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from utils.types import Location


def haversine_km(a: Location, b: Location) -> float:
    radius_km = 6371.0
    dlat = radians(b.latitude - a.latitude)
    dlon = radians(b.longitude - a.longitude)
    lat1 = radians(a.latitude)
    lat2 = radians(b.latitude)
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * radius_km * asin(sqrt(h))


def interpolate_path(start: Location, destination: Location, steps: int = 12) -> list[Location]:
    steps = max(2, steps)
    points: list[Location] = []
    for index in range(steps):
        t = index / (steps - 1)
        points.append(
            Location(
                latitude=start.latitude + (destination.latitude - start.latitude) * t,
                longitude=start.longitude + (destination.longitude - start.longitude) * t,
                label="route-point",
            )
        )
    return points
