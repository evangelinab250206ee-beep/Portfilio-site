"""Train EV energy consumption models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from models.model_manager import ModelManager


FEATURES = ["speed_kmh", "soc_pct", "road_gradient_pct", "temperature_c"]
TARGET = "consumption_kwh_per_100km"


def synthetic_energy(rows: int = 1500) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    speed = rng.uniform(10, 120, rows)
    soc = rng.uniform(10, 100, rows)
    gradient = rng.uniform(-8, 10, rows)
    temp = rng.uniform(-5, 45, rows)
    temp_penalty = np.abs(temp - 22) * 0.12
    aero = 0.0016 * speed**2
    hill = np.maximum(gradient, 0) * 0.75
    regen = np.minimum(gradient, 0) * 0.22
    consumption = np.clip(10.5 + aero + hill + regen + temp_penalty + rng.normal(0, 1.1, rows), 7, 38)
    return pd.DataFrame({"speed_kmh": speed, "soc_pct": soc, "road_gradient_pct": gradient, "temperature_c": temp, TARGET: consumption})


def train(data_path: str | None = None) -> dict[str, float]:
    df = pd.read_csv(data_path) if data_path else synthetic_energy()
    x_train, x_test, y_train, y_test = train_test_split(df[FEATURES], df[TARGET], test_size=0.2, random_state=42)
    gb = GradientBoostingRegressor(random_state=42)
    gb.fit(x_train, y_train)
    gb_pred = gb.predict(x_test)
    nn = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=700, random_state=42))
    nn.fit(x_train, y_train)
    manager = ModelManager()
    manager.save_sklearn("energy_gradient_boosting", gb)
    manager.save_sklearn("energy_neural_network", nn)
    return {
        "gb_mae": float(mean_absolute_error(y_test, gb_pred)),
        "gb_r2": float(r2_score(y_test, gb_pred)),
        "nn_mae": float(mean_absolute_error(y_test, nn.predict(x_test))),
    }


if __name__ == "__main__":
    print(train())
