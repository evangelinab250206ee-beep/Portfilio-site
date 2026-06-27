"""SQLite database setup and repository helpers."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from config.settings import settings
from utils.types import EnergyPrediction, RoutePlan, SensorReading, SolarPrediction, WeatherPrediction


SCHEMA = """
CREATE TABLE IF NOT EXISTS sensor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    temperature_c REAL,
    humidity_pct REAL,
    battery_voltage_v REAL,
    battery_current_a REAL,
    vehicle_speed_kmh REAL,
    battery_soc_pct REAL
);

CREATE TABLE IF NOT EXISTS route_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    start_lat REAL NOT NULL,
    start_lon REAL NOT NULL,
    dest_lat REAL NOT NULL,
    dest_lon REAL NOT NULL,
    distance_km REAL NOT NULL,
    travel_time_min REAL NOT NULL,
    energy_required_kwh REAL NOT NULL,
    path_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weather_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    temperature_c REAL,
    humidity_pct REAL,
    rain_probability_pct REAL,
    wind_speed_mps REAL,
    cloud_cover_pct REAL,
    source TEXT
);

CREATE TABLE IF NOT EXISTS energy_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    consumption_kwh_per_100km REAL NOT NULL,
    remaining_range_km REAL NOT NULL,
    energy_required_kwh REAL NOT NULL,
    source TEXT
);

CREATE TABLE IF NOT EXISTS solar_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    irradiance_w_m2 REAL NOT NULL,
    solar_power_kw REAL NOT NULL,
    source TEXT
);
"""


class EVDatabase:
    def __init__(self, db_path: Path | str = settings.database_path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    def log_sensor_reading(self, reading: SensorReading) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO sensor_logs VALUES
                (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reading.timestamp.isoformat(),
                    reading.location.latitude,
                    reading.location.longitude,
                    reading.temperature_c,
                    reading.humidity_pct,
                    reading.battery_voltage_v,
                    reading.battery_current_a,
                    reading.vehicle_speed_kmh,
                    reading.battery_soc_pct,
                ),
            )

    def log_weather(self, location_lat: float, location_lon: float, weather: WeatherPrediction) -> None:
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO weather_history VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(UTC).isoformat(),
                    location_lat,
                    location_lon,
                    weather.temperature_c,
                    weather.humidity_pct,
                    weather.rain_probability_pct,
                    weather.wind_speed_mps,
                    weather.cloud_cover_pct,
                    weather.source,
                ),
            )

    def log_solar(self, location_lat: float, location_lon: float, solar: SolarPrediction) -> None:
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO solar_predictions VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(UTC).isoformat(),
                    location_lat,
                    location_lon,
                    solar.irradiance_w_m2,
                    solar.solar_power_kw,
                    solar.source,
                ),
            )

    def log_energy(self, energy: EnergyPrediction) -> None:
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO energy_predictions VALUES (NULL, ?, ?, ?, ?, ?)",
                (
                    datetime.now(UTC).isoformat(),
                    energy.consumption_kwh_per_100km,
                    energy.remaining_range_km,
                    energy.energy_required_kwh,
                    energy.source,
                ),
            )

    def log_route(self, route: RoutePlan) -> None:
        path_json = json.dumps([point.__dict__ for point in route.path])
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO route_history VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(UTC).isoformat(),
                    route.start.latitude,
                    route.start.longitude,
                    route.destination.latitude,
                    route.destination.longitude,
                    route.distance_km,
                    route.travel_time_min,
                    route.energy_required_kwh,
                    path_json,
                ),
            )

    def latest_rows(self, table: str, limit: int = 10) -> list[sqlite3.Row]:
        allowed = {"sensor_logs", "route_history", "weather_history", "energy_predictions", "solar_predictions"}
        if table not in allowed:
            raise ValueError(f"Unsupported table: {table}")
        with self.connection() as conn:
            return list(conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)))
