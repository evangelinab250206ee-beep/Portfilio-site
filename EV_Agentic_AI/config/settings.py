"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    database_path: Path = PROJECT_ROOT / "database" / "ev_agentic_ai.sqlite3"
    model_dir: Path = PROJECT_ROOT / "models" / "artifacts"
    data_dir: Path = PROJECT_ROOT / "data"
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
    serial_port: str = os.getenv("EV_SERIAL_PORT", "COM3")
    serial_baudrate: int = int(os.getenv("EV_SERIAL_BAUDRATE", "115200"))
    default_latitude: float = float(os.getenv("EV_DEFAULT_LAT", "12.9716"))
    default_longitude: float = float(os.getenv("EV_DEFAULT_LON", "77.5946"))
    default_soc: float = float(os.getenv("EV_DEFAULT_SOC", "72"))
    usable_battery_kwh: float = float(os.getenv("EV_BATTERY_KWH", "45"))
    charging_threshold_soc: float = float(os.getenv("EV_CHARGE_THRESHOLD_SOC", "25"))


settings = Settings()
