"""Low-dependency GPX extraction, route sampling, and elevation handling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union
from urllib.parse import urlencode
from urllib.request import urlopen
import warnings
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371.0088


def _haversine_km(latitude_a, longitude_a, latitude_b, longitude_b) -> np.ndarray:
    """Vectorised great-circle distance between equal-length coordinate arrays."""
    lat_a, lon_a, lat_b, lon_b = map(np.radians, [latitude_a, longitude_a, latitude_b, longitude_b])
    d_lat, d_lon = lat_b - lat_a, lon_b - lon_a
    a = np.sin(d_lat / 2) ** 2 + np.cos(lat_a) * np.cos(lat_b) * np.sin(d_lon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def read_gpx(gpx_file_path: Union[str, Path]) -> pd.DataFrame:
    """Extract latitude, longitude, optional elevation, and cumulative distance."""
    path = Path(gpx_file_path)
    tree = ET.parse(path)
    points = []
    for element in tree.getroot().iter():
        if element.tag.rsplit("}", 1)[-1] not in {"trkpt", "rtept"}:
            continue
        elevation = next((child.text for child in element if child.tag.rsplit("}", 1)[-1] == "ele"), None)
        points.append({
            "latitude": float(element.attrib["lat"]),
            "longitude": float(element.attrib["lon"]),
            "elevation_m": float(elevation) if elevation is not None else np.nan,
        })
    if len(points) < 2:
        raise ValueError(f"GPX route needs at least two points: {path.name}")
    route = pd.DataFrame(points)
    segment = np.zeros(len(route), dtype="float64")
    segment[1:] = _haversine_km(
        route["latitude"].to_numpy()[:-1], route["longitude"].to_numpy()[:-1],
        route["latitude"].to_numpy()[1:], route["longitude"].to_numpy()[1:],
    )
    route["cumulative_distance_km"] = np.cumsum(segment)
    return route


def sample_route_points(route: pd.DataFrame, sample_distance_km: float = 10.0, maximum_points: int = 100) -> pd.DataFrame:
    """Keep the first/last point and sample evenly by distance, capped in size."""
    total_distance = float(route["cumulative_distance_km"].iloc[-1])
    interval = max(float(sample_distance_km), total_distance / max(maximum_points - 1, 1))
    selected = [0]
    next_distance = interval
    for index, distance in enumerate(route["cumulative_distance_km"].iloc[1:-1], start=1):
        if distance >= next_distance:
            selected.append(index)
            next_distance += interval
    selected.append(len(route) - 1)
    sampled = route.iloc[sorted(set(selected))].copy().reset_index(drop=True)
    sampled["segment_distance_km"] = (
        sampled["cumulative_distance_km"].shift(-1) - sampled["cumulative_distance_km"]
    ).fillna(0.0)
    return sampled


def fetch_missing_elevations(route: pd.DataFrame, batch_size: int = 100) -> pd.DataFrame:
    """Fill missing sampled elevation through Open-Elevation; degrade safely offline."""
    result = route.copy()
    missing = result["elevation_m"].isna()
    if not missing.any():
        return result
    indexes = result.index[missing].tolist()
    try:
        for start in range(0, len(indexes), batch_size):
            chunk = indexes[start:start + batch_size]
            locations = "|".join(f"{result.at[i, 'latitude']},{result.at[i, 'longitude']}" for i in chunk)
            url = "https://api.open-elevation.com/api/v1/lookup?" + urlencode({"locations": locations})
            with urlopen(url, timeout=20) as response:  # nosec B310: fixed public elevation endpoint
                elevations = json.loads(response.read().decode("utf-8"))["results"]
            if len(elevations) != len(chunk):
                raise ValueError("Open-Elevation returned an unexpected result count")
            for index, item in zip(chunk, elevations):
                result.at[index, "elevation_m"] = float(item["elevation"])
    except Exception as error:
        warnings.warn(f"Automatic elevation lookup failed ({error}); using flat/interpolated elevation.")
    result["elevation_m"] = result["elevation_m"].interpolate(limit_direction="both").fillna(0.0)
    return result


def add_elevation_metrics(route: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Calculate elevation gain/loss and slope from the sampled route profile."""
    result = route.copy()
    elevation_change = result["elevation_m"].diff().fillna(0.0)
    horizontal_m = result["segment_distance_km"].shift(1).fillna(0.0).to_numpy() * 1000
    slope = np.divide(elevation_change.to_numpy(), horizontal_m, out=np.zeros(len(result)), where=horizontal_m > 0) * 100
    result["slope_percent"] = slope.astype("float32")
    summary = {
        "total_elevation_gain_m": round(float(elevation_change.clip(lower=0).sum()), 2),
        "total_elevation_loss_m": round(float((-elevation_change.clip(upper=0)).sum()), 2),
        "average_slope_percent": round(float(np.mean(np.abs(slope))), 3),
        "maximum_slope_percent": round(float(np.max(np.abs(slope))), 3),
    }
    return result, summary


def assign_arrival_times(route: pd.DataFrame, departure_date: str, departure_time: str, speed_kmh: float) -> pd.DataFrame:
    """Assign an arrival timestamp at every sampled route point."""
    if speed_kmh <= 0:
        raise ValueError("Estimated travel speed must be greater than zero.")
    result = route.copy()
    departure = pd.Timestamp(f"{departure_date} {departure_time}")
    result["arrival_timestamp"] = departure + pd.to_timedelta(result["cumulative_distance_km"] / speed_kmh, unit="h")
    result["vehicle_speed_kmh"] = np.float32(speed_kmh)
    result["duration_hours"] = (result["segment_distance_km"] / speed_kmh).astype("float32")
    return result
