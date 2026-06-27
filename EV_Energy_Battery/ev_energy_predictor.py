"""CSV-driven EV energy consumption and battery prediction module.

Consumes the results emitted by Phase 2 (``solar_ev_results.csv``) and creates
a route-point energy profile. Route optimisation is intentionally out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import vehicle_config as defaults
except ImportError:
    from . import vehicle_config as defaults

GRAVITY_M_S2 = 9.80665


@dataclass(frozen=True)
class VehicleConfig:
    """Configurable EV road-load and battery properties."""

    vehicle_mass_kg: float = defaults.vehicle_mass_kg
    battery_capacity_kwh: float = defaults.battery_capacity_kwh
    drag_coefficient: float = defaults.drag_coefficient
    frontal_area_m2: float = defaults.frontal_area_m2
    rolling_resistance_coefficient: float = defaults.rolling_resistance_coefficient
    drivetrain_efficiency: float = defaults.drivetrain_efficiency
    air_density_kg_m3: float = defaults.air_density_kg_m3
    initial_battery_percent: float = defaults.initial_battery_percent
    temperature_reference_c: float = defaults.temperature_reference_c
    temperature_penalty_per_c: float = defaults.temperature_penalty_per_c


SOLAR_REQUIRED_COLUMNS = {
    "timestamp", "distance_km", "vehicle_speed_kmh", "solar_energy_wh",
    "ambient_temperature_c", "wind_speed_kmh",
}


def load_solar_results(csv_file_path: Union[str, Path]) -> pd.DataFrame:
    """Load Phase 2 solar results and normalise them for Phase 3.

    The loader reads only the fields needed by the EV model, validates required
    solar fields, and repairs numeric NaNs using timestamp-order interpolation
    followed by median fill. An optional ``elevation_m`` profile is used when
    present. Without it, the route is treated as flat and a warning is emitted.
    """
    path = Path(csv_file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Solar results CSV not found: {path}")
    header = pd.read_csv(path, nrows=0).columns.tolist()
    missing = SOLAR_REQUIRED_COLUMNS.difference(header)
    if missing:
        raise ValueError("Solar results CSV is missing required column(s): " + ", ".join(sorted(missing)))
    usecols = list(SOLAR_REQUIRED_COLUMNS)
    if "elevation_m" in header:
        usecols.append("elevation_m")
    solar = pd.read_csv(path, usecols=usecols)
    if solar.empty:
        raise ValueError("Solar results CSV contains no route points.")

    solar["timestamp"] = pd.to_datetime(solar["timestamp"], errors="coerce")
    invalid_time = int(solar["timestamp"].isna().sum())
    if invalid_time:
        warnings.warn(f"Dropped {invalid_time} row(s) with invalid timestamps.")
        solar = solar.dropna(subset=["timestamp"])
    if solar.empty:
        raise ValueError("No valid timestamps remain in solar results.")
    solar = solar.sort_values("timestamp").reset_index(drop=True)

    numeric = [column for column in usecols if column != "timestamp"]
    solar[numeric] = solar[numeric].apply(pd.to_numeric, errors="coerce")
    missing_values = solar[numeric].isna().sum()
    missing_values = missing_values[missing_values > 0]
    if not missing_values.empty:
        warnings.warn("Filled missing values: " + ", ".join(f"{name} ({count})" for name, count in missing_values.items()))
        solar[numeric] = solar[numeric].interpolate(method="linear", limit_direction="both")
        solar[numeric] = solar[numeric].fillna(solar[numeric].median())
    unresolved = solar[numeric].columns[solar[numeric].isna().any()].tolist()
    if unresolved:
        raise ValueError("Cannot fill required numeric column(s): " + ", ".join(unresolved))

    if "elevation_m" not in solar:
        warnings.warn("No elevation_m column found; treating every route point as 0 m (flat terrain).")
        solar["elevation_m"] = np.float32(0)
    if (solar["distance_km"] < 0).any() or (solar["vehicle_speed_kmh"] < 0).any() or (solar["solar_energy_wh"] < 0).any():
        warnings.warn("Negative distance, speed, or solar-energy values found; they will be clamped to zero.")
    for column in numeric:
        solar[column] = solar[column].astype("float32")
    solar["distance_km"] = solar["distance_km"].clip(lower=0)
    solar["vehicle_speed_kmh"] = solar["vehicle_speed_kmh"].clip(lower=0)
    solar["solar_energy_wh"] = solar["solar_energy_wh"].clip(lower=0)
    return solar


def calculate_energy_consumption(route_points: pd.DataFrame, vehicle: Optional[VehicleConfig] = None) -> pd.DataFrame:
    """Calculate rolling, drag, elevation, and weather-adjusted energy per point."""
    config = vehicle or VehicleConfig()
    if config.vehicle_mass_kg <= 0 or config.battery_capacity_kwh <= 0:
        raise ValueError("Vehicle mass and battery capacity must be greater than zero.")
    if not 0 < config.drivetrain_efficiency <= 1:
        raise ValueError("Drivetrain efficiency must be in the range (0, 1].")

    result = route_points.copy()
    distance_m = result["distance_km"].to_numpy(dtype=float) * 1000
    speed_m_s = result["vehicle_speed_kmh"].to_numpy(dtype=float) / 3.6
    # Wind direction is unavailable, so the conservative headwind assumption is used.
    relative_air_speed = speed_m_s + np.maximum(result["wind_speed_kmh"].to_numpy(dtype=float), 0) / 3.6
    elevation = result["elevation_m"].to_numpy(dtype=float)
    elevation_gain_m = np.maximum(np.diff(elevation, prepend=elevation[0]), 0)

    rolling_force_n = config.vehicle_mass_kg * GRAVITY_M_S2 * config.rolling_resistance_coefficient
    drag_force_n = 0.5 * config.air_density_kg_m3 * config.drag_coefficient * config.frontal_area_m2 * relative_air_speed ** 2
    rolling_energy_wh = rolling_force_n * distance_m / 3600 / config.drivetrain_efficiency
    drag_energy_wh = drag_force_n * distance_m / 3600 / config.drivetrain_efficiency
    elevation_energy_wh = config.vehicle_mass_kg * GRAVITY_M_S2 * elevation_gain_m / 3600 / config.drivetrain_efficiency
    temperature_factor = 1 + np.abs(result["ambient_temperature_c"].to_numpy(dtype=float) - config.temperature_reference_c) * config.temperature_penalty_per_c
    energy_consumed_wh = (rolling_energy_wh + drag_energy_wh + elevation_energy_wh) * temperature_factor

    result["elevation_gain_m"] = elevation_gain_m.astype("float32")
    result["rolling_resistance_force_n"] = np.full(len(result), rolling_force_n, dtype="float32")
    result["aerodynamic_drag_force_n"] = drag_force_n.astype("float32")
    result["rolling_energy_wh"] = rolling_energy_wh.astype("float32")
    result["drag_energy_wh"] = drag_energy_wh.astype("float32")
    result["elevation_energy_wh"] = elevation_energy_wh.astype("float32")
    result["temperature_energy_factor"] = temperature_factor.astype("float32")
    result["energy_consumed_wh"] = energy_consumed_wh.astype("float32")
    result["net_energy_consumption_wh"] = (energy_consumed_wh - result["solar_energy_wh"].to_numpy(dtype=float)).astype("float32")
    return result


def calculate_battery_remaining(route_points: pd.DataFrame, vehicle: Optional[VehicleConfig] = None) -> pd.DataFrame:
    """Apply net route energy point-by-point and return remaining battery state."""
    config = vehicle or VehicleConfig()
    result = route_points.copy()
    capacity_wh = config.battery_capacity_kwh * 1000
    initial_wh = capacity_wh * config.initial_battery_percent / 100
    net = result["net_energy_consumption_wh"].to_numpy(dtype=float)
    remaining_wh = np.clip(initial_wh - np.cumsum(net), 0, capacity_wh)
    result["battery_remaining_wh"] = remaining_wh.astype("float32")
    result["battery_remaining_percent"] = (remaining_wh / capacity_wh * 100).astype("float32")
    return result


def calculate_remaining_range(route_points: pd.DataFrame) -> pd.DataFrame:
    """Estimate remaining range from cumulative net Wh/km at each route point."""
    result = route_points.copy()
    cumulative_distance = result["distance_km"].cumsum().to_numpy(dtype=float)
    cumulative_net_energy = result["net_energy_consumption_wh"].cumsum().to_numpy(dtype=float)
    rate_wh_per_km = np.divide(
        cumulative_net_energy, cumulative_distance,
        out=np.zeros_like(cumulative_net_energy), where=cumulative_distance > 0,
    )
    remaining_range = np.divide(
        result["battery_remaining_wh"].to_numpy(dtype=float), rate_wh_per_km,
        out=np.full(len(result), np.nan), where=rate_wh_per_km > 0,
    )
    result["cumulative_distance_km"] = cumulative_distance.astype("float32")
    result["average_net_energy_wh_per_km"] = rate_wh_per_km.astype("float32")
    result["remaining_range_km"] = remaining_range.astype("float32")
    return result


def predict_trip_energy(route_points: pd.DataFrame, vehicle: Optional[VehicleConfig] = None) -> tuple[pd.DataFrame, dict]:
    """Create per-point EV energy, battery, and range predictions for a route."""
    config = vehicle or VehicleConfig()
    results = calculate_energy_consumption(route_points, config)
    results = calculate_battery_remaining(results, config)
    results = calculate_remaining_range(results)
    final = results.iloc[-1]
    summary = {
        "route_points": int(len(results)),
        "route_distance_km": round(float(final["cumulative_distance_km"]), 3),
        "energy_consumed_kwh": round(float(results["energy_consumed_wh"].sum()) / 1000, 3),
        "solar_energy_generated_kwh": round(float(results["solar_energy_wh"].sum()) / 1000, 3),
        "net_energy_consumption_kwh": round(float(results["net_energy_consumption_wh"].sum()) / 1000, 3),
        "battery_remaining_percent": round(float(final["battery_remaining_percent"]), 2),
        "battery_remaining_kwh": round(float(final["battery_remaining_wh"]) / 1000, 3),
        "remaining_range_km": round(float(final["remaining_range_km"]), 2) if pd.notna(final["remaining_range_km"]) else None,
        "wind_assumption": "Wind speed is treated as headwind because wind direction is unavailable.",
    }
    return results, summary


def save_results(results: pd.DataFrame, summary: dict, output_directory: Union[str, Path] = ".") -> dict:
    """Save ev_energy_results.csv, requested charts, and Markdown summary."""
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "ev_energy_results.csv"
    results.to_csv(csv_path, index=False)
    distance = results["cumulative_distance_km"]
    chart_specs = [
        ("battery_remaining_vs_distance.png", "battery_remaining_percent", "Battery Remaining (%)", "Battery Remaining vs Distance"),
        ("energy_consumption_vs_distance.png", "energy_consumed_wh", "Energy Consumed (Wh)", "Energy Consumption vs Distance"),
        ("elevation_vs_distance.png", "elevation_m", "Elevation (m)", "Elevation vs Distance"),
        ("solar_energy_vs_distance.png", "solar_energy_wh", "Solar Energy Generated (Wh)", "Solar Energy vs Distance"),
        ("remaining_range_vs_distance.png", "remaining_range_km", "Remaining Range (km)", "Remaining Range vs Distance"),
    ]
    saved = {"csv": str(csv_path)}
    for filename, column, ylabel, title in chart_specs:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.plot(distance, results[column], marker="o", markersize=3)
        ax.set(title=title, xlabel="Cumulative Distance (km)", ylabel=ylabel)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        path = output_dir / filename
        fig.savefig(path, dpi=150)
        plt.close(fig)
        saved[filename] = str(path)
    report_path = output_dir / "ev_energy_summary.md"
    report_path.write_text(
        "# EV Energy and Battery Summary\n\n"
        f"- Route points: **{summary['route_points']:,}**\n"
        f"- Route distance: **{summary['route_distance_km']} km**\n"
        f"- Energy consumed: **{summary['energy_consumed_kwh']} kWh**\n"
        f"- Solar energy generated: **{summary['solar_energy_generated_kwh']} kWh**\n"
        f"- Net energy consumption: **{summary['net_energy_consumption_kwh']} kWh**\n"
        f"- Battery remaining: **{summary['battery_remaining_percent']}%** ({summary['battery_remaining_kwh']} kWh)\n"
        f"- Estimated remaining range: **{summary['remaining_range_km']} km**\n\n"
        f"{summary['wind_assumption']}\n",
        encoding="utf-8",
    )
    saved["report"] = str(report_path)
    return saved
