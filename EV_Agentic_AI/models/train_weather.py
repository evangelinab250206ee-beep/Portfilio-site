"""Train weather models using sample or CSV data.

Expected CSV columns:
latitude, longitude, month, hour, temperature_c, humidity_pct, wind_speed_mps, cloud_cover_pct, rain_probability_pct
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor

try:
    from xgboost import XGBRegressor
except Exception:  # pragma: no cover - optional dependency
    XGBRegressor = None

from models.model_manager import ModelManager


FEATURES = ["latitude", "longitude", "month", "hour"]
TARGETS = ["temperature_c", "humidity_pct", "wind_speed_mps", "cloud_cover_pct", "rain_probability_pct"]


def synthetic_weather(rows: int = 1200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    lat = rng.uniform(8, 33, rows)
    lon = rng.uniform(68, 89, rows)
    month = rng.integers(1, 13, rows)
    hour = rng.integers(0, 24, rows)
    temp = 24 + 8 * np.sin((month - 2) / 12 * 2 * np.pi) + 4 * np.sin(hour / 24 * 2 * np.pi) + rng.normal(0, 2, rows)
    humidity = np.clip(65 - 0.5 * (temp - 25) + rng.normal(0, 8, rows), 15, 98)
    cloud = np.clip(35 + humidity * 0.45 + rng.normal(0, 12, rows), 0, 100)
    wind = np.clip(2.5 + rng.normal(0, 1.2, rows), 0, 15)
    rain = np.clip(cloud * 0.55 + humidity * 0.25 + rng.normal(0, 10, rows), 0, 100)
    return pd.DataFrame(
        {
            "latitude": lat,
            "longitude": lon,
            "month": month,
            "hour": hour,
            "temperature_c": temp,
            "humidity_pct": humidity,
            "wind_speed_mps": wind,
            "cloud_cover_pct": cloud,
            "rain_probability_pct": rain,
        }
    )


def train(data_path: str | None = None) -> dict[str, float]:
    df = pd.read_csv(data_path) if data_path else synthetic_weather()
    x_train, x_test, y_train, y_test = train_test_split(df[FEATURES], df[TARGETS], test_size=0.2, random_state=42)
    rf = MultiOutputRegressor(RandomForestRegressor(n_estimators=160, random_state=42))
    rf.fit(x_train, y_train)
    pred = rf.predict(x_test)
    metrics = {"rf_mae": float(mean_absolute_error(y_test, pred)), "rf_r2": float(r2_score(y_test, pred))}
    manager = ModelManager()
    manager.save_sklearn("weather_random_forest", rf)
    if XGBRegressor is not None:
        xgb = MultiOutputRegressor(XGBRegressor(n_estimators=120, max_depth=4, learning_rate=0.08, objective="reg:squarederror"))
        xgb.fit(x_train, y_train)
        metrics["xgb_mae"] = float(mean_absolute_error(y_test, xgb.predict(x_test)))
        manager.save_sklearn("weather_xgboost", xgb)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path)
    args = parser.parse_args()
    print(train(str(args.data) if args.data else None))
