"""Train solar irradiance models with Random Forest and optional Keras LSTM."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from models.model_manager import ModelManager


FEATURES = ["latitude", "longitude", "month", "hour", "cloud_cover_pct"]
TARGET = "irradiance_w_m2"


def synthetic_solar(rows: int = 1600) -> pd.DataFrame:
    rng = np.random.default_rng(13)
    lat = rng.uniform(8, 33, rows)
    lon = rng.uniform(68, 89, rows)
    month = rng.integers(1, 13, rows)
    hour = rng.integers(0, 24, rows)
    cloud = rng.uniform(0, 100, rows)
    daylight = np.maximum(0, np.sin((hour - 6) / 12 * np.pi))
    season = 0.82 + 0.18 * np.sin((month - 2) / 12 * 2 * np.pi)
    irradiance = np.clip(980 * daylight * season * (1 - 0.0075 * cloud) + rng.normal(0, 35, rows), 0, 1050)
    return pd.DataFrame({"latitude": lat, "longitude": lon, "month": month, "hour": hour, "cloud_cover_pct": cloud, TARGET: irradiance})


def train(data_path: str | None = None) -> dict[str, float]:
    df = pd.read_csv(data_path) if data_path else synthetic_solar()
    x_train, x_test, y_train, y_test = train_test_split(df[FEATURES], df[TARGET], test_size=0.2, random_state=42)
    rf = RandomForestRegressor(n_estimators=180, random_state=42)
    rf.fit(x_train, y_train)
    pred = rf.predict(x_test)
    manager = ModelManager()
    manager.save_sklearn("solar_random_forest", rf)
    metrics = {"rf_mae": float(mean_absolute_error(y_test, pred)), "rf_r2": float(r2_score(y_test, pred))}
    try:
        from tensorflow import keras

        series = df[[TARGET]].to_numpy(dtype="float32") / 1000.0
        windows = np.array([series[i : i + 12] for i in range(len(series) - 12)])
        labels = series[12:]
        lstm = keras.Sequential([keras.layers.Input((12, 1)), keras.layers.LSTM(16), keras.layers.Dense(1)])
        lstm.compile(optimizer="adam", loss="mae")
        lstm.fit(windows, labels, epochs=2, verbose=0)
        lstm.save(manager.path("solar_lstm", ".keras"))
    except Exception as exc:  # pragma: no cover - TensorFlow is optional in CI/dev
        metrics["lstm_status"] = f"skipped: {exc}"
    return metrics


if __name__ == "__main__":
    print(train())
