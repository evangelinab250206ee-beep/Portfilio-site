"""Phase 4 orchestration: GPX -> weather -> solar -> EV -> route ranking."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sys
from typing import Optional, Union
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gpx_route_processor import (
    add_elevation_metrics, assign_arrival_times, fetch_missing_elevations,
    read_gpx, sample_route_points,
)
import route_config as settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEATHER_DIR = PROJECT_ROOT / "Weather prediction" / "Weather_dataset" / "WeatherPrediction"
SOLAR_DIR = PROJECT_ROOT / "Solar_EV_Energy"
EV_DIR = PROJECT_ROOT / "EV_Energy_Battery"
for module_dir in [str(WEATHER_DIR), str(SOLAR_DIR), str(EV_DIR)]:
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

from predict import predict_weather  # type: ignore
from solar_ev_predictor import predict_hourly_solar_energy  # type: ignore
from ev_energy_predictor import VehicleConfig, predict_trip_energy  # type: ignore


class _working_directory:
    """Temporarily run the legacy weather module from its expected folder."""
    def __init__(self, directory: Path):
        self.directory = directory
        self.previous: Optional[str] = None

    def __enter__(self):
        self.previous = os.getcwd()
        os.chdir(self.directory)

    def __exit__(self, *_):
        if self.previous is not None:
            os.chdir(self.previous)


class RouteOptimizer:
    """Runs independent route simulations and ranks them with configurable weights."""

    def __init__(self, departure_date: str, departure_time: str, travel_speed_kmh: float,
                 vehicle: Optional[VehicleConfig] = None, use_elevation_api: bool = True,
                 panel_config=None, sample_distance_km: Optional[float] = None,
                 scoring_weights: Optional[dict[str, float]] = None):
        self.departure_date = departure_date
        self.departure_time = departure_time
        self.travel_speed_kmh = travel_speed_kmh
        self.vehicle = vehicle or VehicleConfig()
        self.use_elevation_api = use_elevation_api
        self.panel_config = panel_config
        self.sample_distance_km = sample_distance_km or settings.sample_distance_km
        self.scoring_weights = scoring_weights or {
            "battery": settings.battery_weight, "solar": settings.solar_weight,
            "travel_time": settings.travel_time_weight, "weather": settings.weather_weight,
        }
        self.weather_cache: dict[tuple, dict] = {}
        self.weather_fallback_used = False

    @staticmethod
    def _clear_sky_ghi(timestamp: pd.Timestamp) -> float:
        hour = timestamp.hour + timestamp.minute / 60
        return max(0.0, 900 * np.sin(np.pi * (hour - 6) / 12))

    def _weather_at_point(self, latitude: float, longitude: float, timestamp: pd.Timestamp) -> dict:
        key = (round(latitude, settings.weather_cache_decimal_places), round(longitude, settings.weather_cache_decimal_places), timestamp.floor("h"))
        if key in self.weather_cache:
            return self.weather_cache[key].copy()
        try:
            # The existing predictor emits an expected warning for unseen route cities;
            # suppress it here because lat/lon are intentionally provided per point.
            with redirect_stdout(StringIO()), _working_directory(WEATHER_DIR):
                prediction = predict_weather(
                    city="RoutePoint", date=timestamp.strftime("%Y-%m-%d"),
                    time=timestamp.strftime("%H:%M"), latitude=latitude, longitude=longitude,
                )
            ghi = float(prediction.get("shortwave_radiation", 0.0))
            temperature = float(prediction.get("temperature_2m", 28.0))
            wind = float(prediction.get("wind_speed_10m", 10.0))
            rainfall = float(prediction.get("rain", prediction.get("rain_probability", 0.0)))
            cloud = prediction.get("cloud_cover")
            cloud = float(cloud) if cloud is not None else np.clip(100 * (1 - ghi / max(self._clear_sky_ghi(timestamp), 1)), 0, 100)
            direct = float(prediction.get("direct_radiation", ghi * (1 - cloud / 200)))
            dhi = float(prediction.get("diffuse_radiation", max(0, ghi - direct)))
            dni = float(prediction.get("direct_normal_irradiance", direct / max(0.15, np.sin(np.pi * (timestamp.hour - 6) / 12))))
        except Exception as error:
            self.weather_fallback_used = True
            warnings.warn(f"Weather prediction failed at {latitude:.3f},{longitude:.3f} ({error}); using conservative fallback values.")
            ghi = self._clear_sky_ghi(timestamp) * 0.55
            temperature, wind, rainfall, cloud = 28.0, 10.0, 0.0, 45.0
            direct, dhi, dni = ghi * 0.55, ghi * 0.45, ghi * 0.8
        weather = {
            "temperature": temperature, "rainfall": rainfall, "wind_speed": wind,
            "cloud_cover": float(np.clip(cloud, 0, 100)), "predicted_ghi": max(0, ghi),
            "predicted_direct_radiation": max(0, direct), "predicted_dhi": max(0, dhi),
            "predicted_dni": max(0, dni),
        }
        self.weather_cache[key] = weather
        return weather.copy()

    def _predict_weather(self, route: pd.DataFrame) -> pd.DataFrame:
        weather = [self._weather_at_point(row.latitude, row.longitude, row.arrival_timestamp) for row in route.itertuples(index=False)]
        return pd.concat([route.reset_index(drop=True), pd.DataFrame(weather)], axis=1)

    def process_route(self, gpx_file: Union[str, Path]) -> tuple[pd.DataFrame, dict]:
        """Process one GPX route through all three existing model stages."""
        raw = read_gpx(gpx_file)
        route = sample_route_points(raw, self.sample_distance_km, settings.maximum_route_points)
        if self.use_elevation_api:
            route = fetch_missing_elevations(route, settings.elevation_api_batch_size)
        else:
            route["elevation_m"] = route["elevation_m"].interpolate(limit_direction="both").fillna(0.0)
        route, elevation_summary = add_elevation_metrics(route)
        route = assign_arrival_times(route, self.departure_date, self.departure_time, self.travel_speed_kmh)
        route = self._predict_weather(route)

        solar_input = pd.DataFrame({
            "latitude": route["latitude"], "longitude": route["longitude"],
            "date": route["arrival_timestamp"].dt.strftime("%Y-%m-%d"),
            "time": route["arrival_timestamp"].dt.strftime("%H:%M:%S"),
            "vehicle_speed_kmh": route["vehicle_speed_kmh"],
            "predicted_ghi": route["predicted_ghi"],
            "predicted_direct_radiation": route["predicted_direct_radiation"],
            "predicted_dhi": route["predicted_dhi"], "predicted_dni": route["predicted_dni"],
            "cloud_cover": route["cloud_cover"], "temperature": route["temperature"],
            "wind_speed": route["wind_speed"], "duration_hours": route["duration_hours"],
        })
        solar = predict_hourly_solar_energy(solar_input, panel_config=self.panel_config)
        ev_input = pd.DataFrame({
            "timestamp": route["arrival_timestamp"].astype(str),
            "distance_km": route["segment_distance_km"],
            "vehicle_speed_kmh": route["vehicle_speed_kmh"],
            "solar_energy_wh": solar["solar_energy_wh"],
            "ambient_temperature_c": route["temperature"],
            "wind_speed_kmh": route["wind_speed"],
            "elevation_m": route["elevation_m"],
        })
        ev_results, ev_summary = predict_trip_energy(ev_input, self.vehicle)
        result = pd.concat([route.reset_index(drop=True), solar.add_prefix("solar_"), ev_results.drop(columns=["timestamp", "distance_km", "vehicle_speed_kmh", "solar_energy_wh", "ambient_temperature_c", "wind_speed_kmh", "elevation_m"])], axis=1)
        result["weather_risk"] = np.clip(result["rainfall"].to_numpy(dtype=float) / 5, 0, 1) * 0.7 + result["cloud_cover"].to_numpy(dtype=float) / 100 * 0.3
        result["cumulative_solar_energy_wh"] = result["solar_solar_energy_wh"].cumsum()
        route_name = Path(gpx_file).stem.strip().replace(" ", "_")
        summary = {
            "route": route_name,
            "total_distance_km": round(float(route["cumulative_distance_km"].iloc[-1]), 2),
            **elevation_summary,
            "total_solar_energy_kwh": round(float(result["solar_solar_energy_wh"].sum()) / 1000, 3),
            "total_energy_consumed_kwh": ev_summary["energy_consumed_kwh"],
            "net_energy_consumption_kwh": ev_summary["net_energy_consumption_kwh"],
            "final_battery_remaining_percent": ev_summary["battery_remaining_percent"],
            "final_remaining_range_km": ev_summary["remaining_range_km"],
            "estimated_travel_time_hours": round(float(route["duration_hours"].sum()), 2),
            "average_weather_risk": round(float(result["weather_risk"].mean()), 3),
        }
        return result, summary

    def _score_routes(self, comparison: pd.DataFrame) -> pd.DataFrame:
        """Score normalized route outcomes; higher is better for every component."""
        result = comparison.copy()
        max_solar = max(float(result["total_solar_energy_kwh"].max()), 1e-9)
        min_time = max(float(result["estimated_travel_time_hours"].min()), 1e-9)
        result["battery_component"] = result["final_battery_remaining_percent"] / 100
        result["solar_component"] = result["total_solar_energy_kwh"] / max_solar
        result["travel_time_component"] = min_time / result["estimated_travel_time_hours"].clip(lower=1e-9)
        result["weather_component"] = 1 - result["average_weather_risk"].clip(0, 1)
        result["route_score"] = (
            self.scoring_weights["battery"] * result["battery_component"]
            + self.scoring_weights["solar"] * result["solar_component"]
            + self.scoring_weights["travel_time"] * result["travel_time_component"]
            + self.scoring_weights["weather"] * result["weather_component"]
        )
        return result.sort_values("route_score", ascending=False).reset_index(drop=True)

    def process_routes(self, gpx_directory: Union[str, Path], output_directory: Union[str, Path]) -> pd.DataFrame:
        """Process all GPX files, export route results, rank routes, and report a winner."""
        files = sorted(Path(gpx_directory).glob("*.gpx"))
        if not files:
            raise FileNotFoundError(f"No .gpx files found in {gpx_directory}")
        output = Path(output_directory)
        output.mkdir(parents=True, exist_ok=True)
        summaries = []
        for file in files:
            results, summary = self.process_route(file)
            results.to_csv(output / f"{summary['route']}_results.csv", index=False)
            self._route_charts(results, summary["route"], output)
            summaries.append(summary)
        comparison = self._score_routes(pd.DataFrame(summaries))
        comparison.to_csv(output / "route_comparison.csv", index=False)
        self._comparison_chart(comparison, output)
        self._write_recommendation(comparison, output)
        self._write_report(comparison, output)
        return comparison

    @staticmethod
    def _route_charts(results: pd.DataFrame, route: str, output: Path) -> None:
        charts = [
            ("battery_remaining_percent", "Battery Remaining (%)", "Battery Remaining vs Distance"),
            ("cumulative_solar_energy_wh", "Cumulative Solar Energy (Wh)", "Solar Energy vs Distance"),
            ("elevation_m", "Elevation (m)", "Elevation vs Distance"),
            ("weather_risk", "Weather Risk (0–1)", "Weather Risk vs Distance"),
        ]
        for column, ylabel, title in charts:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(results["cumulative_distance_km"], results[column])
            ax.set(title=f"{route}: {title}", xlabel="Distance (km)", ylabel=ylabel)
            ax.grid(alpha=0.25); fig.tight_layout()
            fig.savefig(output / f"{route}_{column}.png", dpi=150); plt.close(fig)

    @staticmethod
    def _comparison_chart(comparison: pd.DataFrame, output: Path) -> None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(comparison["route"], comparison["route_score"], color="#2563eb")
        ax.set(title="Route Comparison Score", xlabel="Route", ylabel="Score")
        for index, value in enumerate(comparison["route_score"]):
            ax.text(index, value, f"{value:.3f}", ha="center", va="bottom")
        fig.tight_layout(); fig.savefig(output / "route_comparison_bar_chart.png", dpi=150); plt.close(fig)

    def _write_recommendation(self, comparison: pd.DataFrame, output: Path) -> None:
        best = comparison.iloc[0].to_dict()
        reason = (
            f"Highest weighted score ({best['route_score']:.3f}) from battery reserve, solar gain, "
            f"travel time, and weather-risk components."
        )
        payload = {
            "best_route": best["route"], "reason": reason,
            "expected_battery_remaining_percent": best["final_battery_remaining_percent"],
            "expected_solar_gain_kwh": best["total_solar_energy_kwh"],
            "expected_travel_time_hours": best["estimated_travel_time_hours"],
            "expected_weather_conditions": {"average_weather_risk": best["average_weather_risk"]},
            "score": best["route_score"],
            "weather_model_fallback_used": self.weather_fallback_used,
        }
        (output / "best_route.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _write_report(comparison: pd.DataFrame, output: Path) -> None:
        best = comparison.iloc[0]
        lines = ["# Solar-Assisted EV Route Analysis", ""]
        for row in comparison.itertuples(index=False):
            lines.extend([
                f"## {row.route} Summary", f"- Distance: {row.total_distance_km} km",
                f"- Travel time: {row.estimated_travel_time_hours} hours",
                f"- Solar energy: {row.total_solar_energy_kwh} kWh",
                f"- Energy consumed: {row.total_energy_consumed_kwh} kWh",
                f"- Battery remaining: {row.final_battery_remaining_percent}%", "",
            ])
        lines.extend([
            "## Recommended Route", f"**{best['route']}** has the highest weighted score ({best['route_score']:.3f}).",
            f"Battery advantage: {best['final_battery_remaining_percent']}% remaining; solar gain: {best['total_solar_energy_kwh']} kWh.",
            f"Weather risk: {best['average_weather_risk']}; travel time: {best['estimated_travel_time_hours']} hours.",
        ])
        (output / "route_summary.md").write_text("\n".join(lines), encoding="utf-8")
