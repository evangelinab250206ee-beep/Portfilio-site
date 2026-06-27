"""OpenStreetMap Nominatim geocoding helpers."""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import settings
from utils.types import Location


@dataclass(frozen=True)
class GeocodeResult:
    location: Location
    display_name: str


def geocode_place(query: str, limit: int = 8) -> list[GeocodeResult]:
    """Search OpenStreetMap Nominatim for a place name.

    Network failures return an empty list so the dashboard remains usable offline.
    """

    query = query.strip()
    if not query:
        return []
    try:
        import requests

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "jsonv2", "limit": limit},
            headers={"User-Agent": "EV-Agentic-AI/1.0"},
            timeout=10,
        )
        response.raise_for_status()
        results = []
        for item in response.json():
            results.append(
                GeocodeResult(
                    location=Location(float(item["lat"]), float(item["lon"]), item.get("display_name", query)),
                    display_name=item.get("display_name", query),
                )
            )
        return results
    except Exception:
        return []


def configured_current_location() -> Location:
    return Location(settings.default_latitude, settings.default_longitude, "Current location")
