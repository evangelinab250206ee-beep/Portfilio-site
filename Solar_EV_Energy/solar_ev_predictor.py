"""Solar-assisted EV energy generation model.

This module estimates photovoltaic energy available from an EV roof panel.
It deliberately does not model battery depletion, charging state, or vehicle
traction demand.  Those can be connected later through ``trip_energy_demand_kwh``
when a battery or route-energy model is available.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import importlib.util
from math import acos, cos, degrees, radians, sin
from pathlib import Path
from typing import Iterable, Mapping, Optional, Union
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load the adjacent configuration explicitly.  Several project phases have a
# config.py, so a plain ``from config import ...`` can import another phase's
# settings when this module is orchestrated from Phase 4.
_config_spec = importlib.util.spec_from_file_location(
    "solar_ev_panel_config", Path(__file__).with_name("config.py")
)
if _config_spec is None or _config_spec.loader is None:
    raise ImportError("Could not load Solar_EV_Energy/config.py")
_panel_config = importlib.util.module_from_spec(_config_spec)
_config_spec.loader.exec_module(_panel_config)
azimuth_angle = _panel_config.azimuth_angle
cloud_cover_loss_strength = _panel_config.cloud_cover_loss_strength
ground_albedo = _panel_config.ground_albedo
mppt_efficiency = _panel_config.mppt_efficiency
nominal_operating_cell_temperature = _panel_config.nominal_operating_cell_temperature
panel_area = _panel_config.panel_area
panel_efficiency = _panel_config.panel_efficiency
temperature_coefficient = _panel_config.temperature_coefficient
tilt_angle = _panel_config.tilt_angle


@dataclass(frozen=True)
class PanelConfig:
    """Physical and electrical parameters for the EV's solar panel."""

    panel_area_m2: float = panel_area
    panel_efficiency: float = panel_efficiency
    mppt_efficiency: float = mppt_efficiency
    temperature_coefficient: float = temperature_coefficient
    tilt_angle_deg: float = tilt_angle
    azimuth_angle_deg: float = azimuth_angle
    nominal_operating_cell_temperature_c: float = nominal_operating_cell_temperature
    ground_albedo: float = ground_albedo
    cloud_cover_loss_strength: float = cloud_cover_loss_strength


WeatherRecord = Mapping[str, Union[str, float, int]]

WEATHER_CSV_REQUIRED_COLUMNS = {
    "timestamp", "latitude", "longitude", "temperature_2m", "precipitation",
    "wind_speed_10m", "cloud_cover", "shortwave_radiation", "direct_radiation",
    "diffuse_radiation", "direct_normal_irradiance",
}


def load_weather_predictions(csv_file_path: Union[str, Path]) -> pd.DataFrame:
    """Load, validate, and map Weather Prediction System CSV output.

    Required source columns are documented in ``WEATHER_CSV_REQUIRED_COLUMNS``.
    The result is a compact, normalized DataFrame accepted directly by
    :func:`predict_trip_solar_energy`. NaN weather values are time-interpolated,
    then filled with a column median; invalid timestamps are discarded with a
    warning. ``vehicle_speed_kmh`` is optional and defaults to 0 (or may be
    supplied later by ``run_pipeline.py``).
    """
    csv_path = Path(csv_file_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Weather prediction CSV not found: {csv_path}")

    # usecols prevents unrelated Weather Prediction System fields from being
    # loaded into memory when processing large route files.
    available_columns = pd.read_csv(csv_path, nrows=0).columns.tolist()
    missing = WEATHER_CSV_REQUIRED_COLUMNS.difference(available_columns)
    if missing:
        raise ValueError(
            "Weather prediction CSV is missing required column(s): "
            + ", ".join(sorted(missing))
        )
    source_columns = list(WEATHER_CSV_REQUIRED_COLUMNS)
    if "vehicle_speed_kmh" in available_columns:
        source_columns.append("vehicle_speed_kmh")
    weather = pd.read_csv(csv_path, usecols=source_columns)
    if weather.empty:
        raise ValueError("Weather prediction CSV contains no route points.")

    weather["timestamp"] = pd.to_datetime(weather["timestamp"], errors="coerce")
    invalid_timestamps = int(weather["timestamp"].isna().sum())
    if invalid_timestamps:
        warnings.warn(f"Dropped {invalid_timestamps} row(s) with invalid timestamp values.")
        weather = weather.dropna(subset=["timestamp"])
    if weather.empty:
        raise ValueError("No valid timestamp values remain in the weather prediction CSV.")
    weather = weather.sort_values("timestamp").reset_index(drop=True)

    numeric_columns = [column for column in source_columns if column != "timestamp"]
    weather[numeric_columns] = weather[numeric_columns].apply(pd.to_numeric, errors="coerce")
    nan_counts = weather[numeric_columns].isna().sum()
    columns_with_nans = nan_counts[nan_counts > 0]
    if not columns_with_nans.empty:
        warnings.warn(
            "Missing/non-numeric weather values were time-interpolated and median-filled: "
            + ", ".join(f"{column} ({count})" for column, count in columns_with_nans.items())
        )
        weather[numeric_columns] = weather[numeric_columns].interpolate(
            method="linear", limit_direction="both"
        )
        weather[numeric_columns] = weather[numeric_columns].fillna(weather[numeric_columns].median())
    if weather[numeric_columns].isna().any().any():
        bad = weather[numeric_columns].columns[weather[numeric_columns].isna().any()].tolist()
        raise ValueError("Cannot fill required numeric column(s): " + ", ".join(bad))

    invalid_messages = []
    if ((weather["cloud_cover"] < 0) | (weather["cloud_cover"] > 100)).any():
        invalid_messages.append("cloud_cover outside 0–100% (the solar model will clamp it)")
    for column in ["shortwave_radiation", "direct_radiation", "diffuse_radiation", "direct_normal_irradiance"]:
        if (weather[column] < 0).any():
            invalid_messages.append(f"negative {column} values (the solar model will clamp them)")
    if (weather["wind_speed_10m"] < 0).any():
        invalid_messages.append("negative wind_speed_10m values")
    if ((weather["latitude"] < -90) | (weather["latitude"] > 90)).any() or ((weather["longitude"] < -180) | (weather["longitude"] > 180)).any():
        invalid_messages.append("latitude/longitude outside valid geographic ranges")
    if invalid_messages:
        warnings.warn("Invalid weather data detected: " + "; ".join(invalid_messages))

    # Map Weather Prediction System output names to the established solar API.
    mapped = pd.DataFrame({
        "latitude": weather["latitude"].astype("float32"),
        "longitude": weather["longitude"].astype("float32"),
        "date": weather["timestamp"].dt.strftime("%Y-%m-%d"),
        "time": weather["timestamp"].dt.strftime("%H:%M:%S"),
        "vehicle_speed_kmh": weather.get("vehicle_speed_kmh", pd.Series(0.0, index=weather.index)).astype("float32"),
        "predicted_ghi": weather["shortwave_radiation"].astype("float32"),
        "predicted_direct_radiation": weather["direct_radiation"].astype("float32"),
        "predicted_dhi": weather["diffuse_radiation"].astype("float32"),
        "predicted_dni": weather["direct_normal_irradiance"].astype("float32"),
        "cloud_cover": weather["cloud_cover"].astype("float32"),
        "temperature": weather["temperature_2m"].astype("float32"),
        "wind_speed": weather["wind_speed_10m"].astype("float32"),
        # Retained for traceability even though rainfall does not affect the
        # current solar formula.
        "precipitation": weather["precipitation"].astype("float32"),
    })
    # A timestamped weather file normally represents consecutive route
    # intervals. Infer each interval length without requiring manual values.
    interval_hours = weather["timestamp"].shift(-1).sub(weather["timestamp"]).dt.total_seconds() / 3600
    default_interval = interval_hours[interval_hours > 0].median()
    mapped["duration_hours"] = interval_hours.where(interval_hours > 0, default_interval)
    mapped["duration_hours"] = mapped["duration_hours"].fillna(1.0).astype("float32")
    return mapped


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _timestamp(date: str, time: str) -> datetime:
    return datetime.fromisoformat(f"{date} {time}")


def _solar_position(latitude: float, longitude: float, timestamp: datetime) -> tuple[float, float]:
    """Approximate local solar elevation and azimuth in degrees.

    ``timestamp`` is treated as local civil time at the supplied longitude.
    This is sufficiently accurate for an energy estimate; a future route module
    can replace it with GPS timestamp/timezone-aware solar positioning.
    """
    day = timestamp.timetuple().tm_yday
    local_hour = timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600
    # Equation of time (minutes) and local-standard-meridian correction.
    # The timezone is not an input yet, so the nearest 15° meridian is used.
    # That keeps a local clock time close to local solar time for route estimates.
    gamma = 2 * np.pi / 365 * (day - 1 + (local_hour - 12) / 24)
    equation_of_time = 229.18 * (
        0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma)
    )
    standard_meridian = round(longitude / 15) * 15
    solar_time = local_hour + (equation_of_time + 4 * (longitude - standard_meridian)) / 60
    hour_angle = radians(15 * (solar_time - 12))
    declination = (
        0.006918 - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2 * gamma) + 0.000907 * np.sin(2 * gamma)
        - 0.002697 * np.cos(3 * gamma) + 0.00148 * np.sin(3 * gamma)
    )
    lat = radians(latitude)
    cos_zenith = _bounded(
        sin(lat) * sin(declination) + cos(lat) * cos(declination) * cos(hour_angle), -1, 1
    )
    elevation = degrees(np.pi / 2 - acos(cos_zenith))
    # Solar azimuth: clockwise from north.
    azimuth = degrees(np.arctan2(
        np.sin(hour_angle),
        np.cos(hour_angle) * np.sin(lat) - np.tan(declination) * np.cos(lat),
    )) + 180
    return elevation, azimuth % 360


def _plane_of_array_irradiance(
    ghi: float, direct_radiation: float, dhi: float, dni: float,
    solar_elevation_deg: float, solar_azimuth_deg: float, config: PanelConfig,
) -> tuple[float, float]:
    """Return (plane-of-array irradiance, tilt factor) in W/m²."""
    if solar_elevation_deg <= 0 or ghi <= 0:
        return 0.0, 0.0
    tilt = radians(config.tilt_angle_deg)
    solar_zenith = radians(90 - solar_elevation_deg)
    azimuth_delta = radians(solar_azimuth_deg - config.azimuth_angle_deg)
    cos_incidence = (
        cos(solar_zenith) * cos(tilt)
        + sin(solar_zenith) * sin(tilt) * cos(azimuth_delta)
    )
    beam = max(0.0, dni) * max(0.0, cos_incidence)
    # If DNI is unavailable but direct horizontal radiation is available,
    # preserve a useful estimate without manufacturing extra irradiance.
    if dni <= 0 and direct_radiation > 0:
        beam = max(0.0, direct_radiation) * max(0.0, cos(tilt))
    diffuse = max(0.0, dhi) * (1 + cos(tilt)) / 2
    reflected = max(0.0, ghi) * config.ground_albedo * (1 - cos(tilt)) / 2
    poa = beam + diffuse + reflected
    return poa, poa / ghi if ghi > 0 else 0.0


def predict_solar_power(
    latitude: float, longitude: float, date: str, time: str, vehicle_speed_kmh: float,
    predicted_ghi: float, predicted_direct_radiation: float, predicted_dhi: float,
    predicted_dni: float, cloud_cover: float, temperature: float, wind_speed: float,
    panel_config: Optional[PanelConfig] = None,
) -> dict:
    """Predict instantaneous roof-panel power for one weather/location point.

    Cloud correction uses ``1 - cloud_cover/100 * cloud_cover_loss_strength``.
    Effective irradiance follows the required GHI × cloud correction formula,
    then is tilt-adjusted using direct, diffuse, and DNI radiation.
    """
    config = panel_config or PanelConfig()
    timestamp = _timestamp(date, time)
    cloud = _bounded(cloud_cover, 0, 100)
    ghi = max(0.0, float(predicted_ghi))
    elevation, solar_azimuth = _solar_position(float(latitude), float(longitude), timestamp)
    poa, tilt_factor = _plane_of_array_irradiance(
        ghi, float(predicted_direct_radiation), float(predicted_dhi), float(predicted_dni),
        elevation, solar_azimuth, config,
    )
    cloud_factor = 1 - (cloud / 100) * config.cloud_cover_loss_strength
    base_effective_irradiance = ghi * cloud_factor
    effective_irradiance = base_effective_irradiance * tilt_factor
    if elevation <= 0:
        effective_irradiance = 0.0
    # NOCT model. Wind is included as a conservative cooling adjustment.
    cell_temperature = float(temperature) + (
        (config.nominal_operating_cell_temperature_c - 20) / 800
    ) * effective_irradiance - min(max(float(wind_speed), 0), 30) * 0.25
    temperature_factor = max(0.0, 1 + config.temperature_coefficient * (cell_temperature - 25))
    adjusted_panel_efficiency = config.panel_efficiency * temperature_factor
    solar_power_w = effective_irradiance * config.panel_area_m2 * adjusted_panel_efficiency
    net_solar_power_w = solar_power_w * config.mppt_efficiency

    return {
        "timestamp": timestamp.isoformat(sep=" "),
        "latitude": float(latitude), "longitude": float(longitude),
        "vehicle_speed_kmh": float(vehicle_speed_kmh),
        "ghi_w_m2": ghi, "direct_radiation_w_m2": max(0.0, float(predicted_direct_radiation)),
        "dhi_w_m2": max(0.0, float(predicted_dhi)), "dni_w_m2": max(0.0, float(predicted_dni)),
        "cloud_cover_percent": cloud, "ambient_temperature_c": float(temperature),
        "wind_speed_kmh": float(wind_speed), "solar_elevation_deg": round(elevation, 3),
        "solar_azimuth_deg": round(solar_azimuth, 3), "poa_irradiance_w_m2": round(poa, 3),
        "tilt_factor": round(tilt_factor, 5), "cloud_correction_factor": round(cloud_factor, 5),
        "effective_irradiance_w_m2": round(effective_irradiance, 3),
        "cell_temperature_c": round(cell_temperature, 3),
        "temperature_derating_factor": round(temperature_factor, 5),
        "adjusted_panel_efficiency": round(adjusted_panel_efficiency, 5),
        "solar_power_w": round(solar_power_w, 3),
        "net_solar_power_w": round(net_solar_power_w, 3),
    }


def predict_hourly_solar_energy(
    weather_points: Iterable[WeatherRecord], panel_config: Optional[PanelConfig] = None,
) -> pd.DataFrame:
    """Calculate power and Wh for time-indexed weather points.

    Each record needs the inputs accepted by ``predict_solar_power`` and may
    include ``duration_hours`` (default: 1).  This lets a route later supply
    shorter GPX segments without changing the public API.
    """
    rows = []
    # itertuples avoids materialising a second full list of dictionaries when
    # the loader provides thousands of route points in a DataFrame.
    points = (
        (row._asdict() for row in weather_points.itertuples(index=False))
        if isinstance(weather_points, pd.DataFrame) else weather_points
    )
    for point in points:
        result = predict_solar_power(
            latitude=point["latitude"], longitude=point["longitude"], date=str(point["date"]),
            time=str(point["time"]), vehicle_speed_kmh=point.get("vehicle_speed_kmh", 0),
            predicted_ghi=point["predicted_ghi"],
            predicted_direct_radiation=point["predicted_direct_radiation"],
            predicted_dhi=point["predicted_dhi"], predicted_dni=point["predicted_dni"],
            cloud_cover=point["cloud_cover"], temperature=point["temperature"],
            wind_speed=point["wind_speed"], panel_config=panel_config,
        )
        duration = max(0.0, float(point.get("duration_hours", 1.0)))
        result["duration_hours"] = duration
        result["solar_energy_wh"] = round(result["net_solar_power_w"] * duration, 3)
        result["solar_energy_kwh"] = round(result["solar_energy_wh"] / 1000, 5)
        result["distance_km"] = round(result["vehicle_speed_kmh"] * duration, 3)
        rows.append(result)
    return pd.DataFrame(rows)


def predict_trip_solar_energy(
    weather_points: Iterable[WeatherRecord], panel_config: Optional[PanelConfig] = None,
    trip_energy_demand_kwh: Optional[float] = None,
) -> tuple[pd.DataFrame, dict]:
    """Predict total route solar energy, without calculating battery depletion."""
    results = predict_hourly_solar_energy(weather_points, panel_config)
    total_wh = float(results["solar_energy_wh"].sum()) if not results.empty else 0.0
    daily_wh = (
        results.assign(date=pd.to_datetime(results["timestamp"]).dt.date)
        .groupby("date")["solar_energy_wh"].sum().to_dict() if not results.empty else {}
    )
    contribution = None
    if trip_energy_demand_kwh is not None and trip_energy_demand_kwh > 0:
        contribution = total_wh / (trip_energy_demand_kwh * 1000) * 100
    summary = {
        "total_trip_solar_energy_wh": round(total_wh, 3),
        "total_trip_solar_energy_kwh": round(total_wh / 1000, 5),
        "daily_solar_energy_wh": {str(day): round(value, 3) for day, value in daily_wh.items()},
        "total_distance_km": round(float(results["distance_km"].sum()), 3) if not results.empty else 0.0,
        "solar_contribution_percentage": round(contribution, 3) if contribution is not None else None,
        "note": "Solar contribution needs an externally supplied trip energy demand; battery depletion is not calculated.",
    }
    return results, summary


def save_results(results: pd.DataFrame, summary: dict, output_directory: Union[str, Path]) -> dict:
    """Save CSV, five PNG graphs, and a Markdown summary report."""
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "solar_ev_results.csv"
    results.to_csv(csv_path, index=False)
    plot_paths = _create_visualizations(results, output_dir)
    report_path = output_dir / "solar_ev_summary.md"
    report = ["# Solar-Assisted EV Energy Summary", "", f"- Total solar energy: **{summary['total_trip_solar_energy_wh']} Wh** ({summary['total_trip_solar_energy_kwh']} kWh)", f"- Total route distance represented: **{summary['total_distance_km']} km**"]
    if summary["solar_contribution_percentage"] is None:
        report.append("- Solar contribution: not calculated (no external trip-energy demand supplied).")
    else:
        report.append(f"- Solar contribution: **{summary['solar_contribution_percentage']}%** of supplied trip-energy demand.")
    report.extend(["", "## Daily solar energy (Wh)"] + [f"- {day}: {energy}" for day, energy in summary["daily_solar_energy_wh"].items()] + ["", summary["note"]])
    report_path.write_text("\n".join(report), encoding="utf-8")
    return {"csv": str(csv_path), "report": str(report_path), **plot_paths}


def _create_visualizations(results: pd.DataFrame, output_dir: Path) -> dict:
    """Create requested charts. Empty inputs produce no charts."""
    if results.empty:
        return {}
    frame = results.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    charts = {
        "solar_power_vs_time.png": ("net_solar_power_w", "Solar Power (W)", "Solar Power vs Time"),
        "solar_energy_vs_time.png": ("solar_energy_wh", "Solar Energy (Wh)", "Solar Energy vs Time"),
        "ghi_vs_time.png": ("ghi_w_m2", "GHI (W/m²)", "GHI vs Time"),
    }
    paths = {}
    for filename, (column, ylabel, title) in charts.items():
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.plot(frame["timestamp"], frame[column], marker="o")
        ax.set(title=title, xlabel="Time", ylabel=ylabel)
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout(); path = output_dir / filename; fig.savefig(path, dpi=150); plt.close(fig)
        paths[filename] = str(path)
    for filename, x, xlabel, title in [
        ("cloud_cover_vs_solar_output.png", "cloud_cover_percent", "Cloud Cover (%)", "Cloud Cover vs Solar Output"),
        ("temperature_vs_solar_efficiency.png", "ambient_temperature_c", "Temperature (°C)", "Temperature vs Solar Efficiency"),
    ]:
        y = "net_solar_power_w" if "cloud" in filename else "adjusted_panel_efficiency"
        ylabel = "Net Solar Power (W)" if "cloud" in filename else "Adjusted Panel Efficiency"
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.scatter(frame[x], frame[y], alpha=0.75)
        ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
        fig.tight_layout(); path = output_dir / filename; fig.savefig(path, dpi=150); plt.close(fig)
        paths[filename] = str(path)
    return paths
