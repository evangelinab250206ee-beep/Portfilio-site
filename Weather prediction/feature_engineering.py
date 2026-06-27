"""
feature_engineering.py
-------------------------
Builds the feature matrix shared by all models (regression + classification).

Features:
  - hour, day, month, day_of_week     (raw time features, as requested)
  - cyclical encodings of hour/month/day_of_week (sin/cos), so the model
    understands hour=23 is close to hour=0, Dec is close to Jan, etc.
  - latitude, longitude               (location)
  - city                              (one-hot encoded)

Targets:
  - temperature_2m       (regression)
  - shortwave_radiation  (regression)
  - rain_flag            (classification: 1 if rain (mm) > threshold)
  - wind_speed_10m       (regression, for the predict_weather() output)
"""

import numpy as np
import pandas as pd

REGRESSION_TARGETS = ["temperature_2m", "shortwave_radiation", "wind_speed_10m"]
CLASSIFICATION_TARGET = "rain_flag"

RAW_TIME_FEATURES = ["hour", "day", "month", "day_of_week"]

BASE_FEATURE_COLUMNS = RAW_TIME_FEATURES + [
    "latitude",
    "longitude",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
    "dow_sin",
    "dow_cos",
]


def add_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds sin/cos encodings for hour, month, and day_of_week."""
    df = df.copy()
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    return df


def build_features(df: pd.DataFrame):
    """
    Builds the feature matrix X (raw time features + cyclical encodings +
    lat/lon + one-hot city). Returns (X, feature_cols, city_dummy_cols).
    """
    df = add_cyclical_features(df)

    city_dummies = pd.get_dummies(df["city"], prefix="city")
    feature_cols = BASE_FEATURE_COLUMNS + list(city_dummies.columns)

    X = pd.concat([df[BASE_FEATURE_COLUMNS], city_dummies], axis=1)
    return X, feature_cols, list(city_dummies.columns)


def build_regression_targets(df: pd.DataFrame) -> pd.DataFrame:
    return df[REGRESSION_TARGETS]


def build_classification_target(df: pd.DataFrame) -> pd.Series:
    return df[CLASSIFICATION_TARGET]
