"""Geocoding, road-route retrieval, and temporary GPX creation for the web app."""

from __future__ import annotations

from pathlib import Path
from typing import Union
import xml.etree.ElementTree as ET

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
HEADERS = {"User-Agent": "SolarAssistedEVRouteOptimization/1.0 (academic-project)"}


def geocode_city(city: str) -> dict:
    """Resolve a city name with OpenStreetMap Nominatim."""
    response = requests.get(
        NOMINATIM_URL, params={"q": city, "format": "jsonv2", "limit": 1},
        headers=HEADERS, timeout=20,
    )
    response.raise_for_status()
    matches = response.json()
    if not matches:
        raise ValueError(f"Could not geocode '{city}'. Try a more specific city name.")
    match = matches[0]
    return {"latitude": float(match["lat"]), "longitude": float(match["lon"]), "label": match["display_name"]}


def _request_route(coordinates: list[tuple[float, float]]) -> list[dict]:
    encoded = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coordinates)
    response = requests.get(
        f"{OSRM_URL}/{encoded}",
        params={"alternatives": "true", "overview": "full", "geometries": "geojson", "steps": "false"},
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != "Ok" or not payload.get("routes"):
        raise ValueError("Routing service could not create a driving route for these cities.")
    return payload["routes"]


def generate_route_alternatives(start: dict, destination: dict, alternatives: int = 3) -> list[dict]:
    """Return up to three road-route alternatives, requesting detour routes if needed."""
    routes = _request_route([(start["latitude"], start["longitude"]), (destination["latitude"], destination["longitude"])])
    accepted: list[dict] = []
    seen: set[tuple] = set()

    def add(candidate: dict) -> None:
        coordinates = candidate["geometry"]["coordinates"]
        signature = (round(candidate["distance"] / 1000, 1), len(coordinates))
        if signature not in seen and len(accepted) < alternatives:
            seen.add(signature)
            accepted.append(candidate)

    for route in routes:
        add(route)
    # Public OSRM often returns fewer than three alternatives. Request genuine
    # road routes via small midpoint detours instead of drawing artificial lines.
    midpoint_lat = (start["latitude"] + destination["latitude"]) / 2
    midpoint_lon = (start["longitude"] + destination["longitude"]) / 2
    offsets = [(0.10, 0.0), (-0.10, 0.0), (0.0, 0.12), (0.0, -0.12), (0.18, 0.10)]
    for lat_offset, lon_offset in offsets:
        if len(accepted) >= alternatives:
            break
        try:
            for route in _request_route([
                (start["latitude"], start["longitude"]),
                (midpoint_lat + lat_offset, midpoint_lon + lon_offset),
                (destination["latitude"], destination["longitude"]),
            ]):
                add(route)
        except requests.RequestException:
            continue
    if not accepted:
        raise ValueError("No road-route alternatives could be generated.")
    results = []
    for number, route in enumerate(accepted, start=1):
        results.append({
            "route": f"Route {chr(64 + number)}",
            "distance_km": round(float(route["distance"]) / 1000, 3),
            "duration_hours": round(float(route["duration"]) / 3600, 3),
            "coordinates": [(float(lat), float(lon)) for lon, lat in route["geometry"]["coordinates"]],
        })
    return results


def write_routes_to_gpx(routes: list[dict], directory: Union[str, Path]) -> Path:
    """Write service routes as GPX tracks consumable by the existing Phase 4 module."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    for route in routes:
        safe_name = route["route"].lower().replace(" ", "_")
        gpx = ET.Element("gpx", version="1.1", creator="Solar-Assisted EV Dashboard")
        track = ET.SubElement(gpx, "trk"); ET.SubElement(track, "name").text = route["route"]
        segment = ET.SubElement(track, "trkseg")
        for latitude, longitude in route["coordinates"]:
            ET.SubElement(segment, "trkpt", lat=f"{latitude:.7f}", lon=f"{longitude:.7f}")
        ET.ElementTree(gpx).write(target / f"{safe_name}.gpx", encoding="utf-8", xml_declaration=True)
    return target
