"""
predict.py
------------
Loads the trained models (saved by train.py) and exposes predict_weather()
for inference: given a city, date, and time, returns predicted temperature,
solar radiation, rain probability, and wind speed.

Usage:
    from predict import predict_weather

    result = predict_weather(city="Bengaluru", date="2026-07-15", time="13:00")
    print(result)
    # {'temperature_2m': 28.4, 'shortwave_radiation': 540.2,
    #  'rain_probability': 0.32, 'rain_prediction': 'No',
    #  'wind_speed_10m': 9.3}
"""

import os
import glob
import json
import joblib
import numpy as np
import pandas as pd

MODELS_DIR = "Models"
WEATHER_DATA_DIR = "WeatherData"

_SCHEMA_CACHE = None
_MODEL_CACHE = {}
_CITY_COORDS_CACHE = None


def _load_schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        schema_path = os.path.join(MODELS_DIR, "feature_schema.json")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(
                f"'{schema_path}' not found. Run train.py first to train and "
                "save models before calling predict_weather()."
            )
        with open(schema_path, "r") as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def _load_model(key: str):
    """Loads (and caches) a saved model. `key` is e.g. 'temperature_2m' or 'rain_flag'."""
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    schema = _load_schema()

    if key == schema["classification_target"]:
        model_name = schema["best_classifier"]
    elif key in schema["best_model_per_regression_target"]:
        model_name = schema["best_model_per_regression_target"][key]
    else:
        raise ValueError(
            f"Unknown target '{key}'. Valid targets: "
            f"{schema['regression_targets'] + [schema['classification_target']]}"
        )

    model_path = os.path.join(MODELS_DIR, f"{key}_{model_name}.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file '{model_path}' not found. Re-run train.py.")

    model = joblib.load(model_path)
    _MODEL_CACHE[key] = model
    return model


def _load_city_coordinates() -> dict:
    """Builds city -> (latitude, longitude) by reading each CSV's metadata block."""
    global _CITY_COORDS_CACHE
    if _CITY_COORDS_CACHE is not None:
        return _CITY_COORDS_CACHE

    from data_loader import city_name_from_filename

    coords = {}
    for filepath in glob.glob(os.path.join(WEATHER_DATA_DIR, "*.csv")):
        city = city_name_from_filename(filepath)
        with open(filepath, "r", encoding="utf-8") as fh:
            first_line = fh.readline().strip().lower()
        if first_line.startswith("latitude"):
            meta = pd.read_csv(filepath, nrows=1)
            lat = meta["latitude"].iloc[0] if "latitude" in meta.columns else np.nan
            lon = meta["longitude"].iloc[0] if "longitude" in meta.columns else np.nan
        else:
            df = pd.read_csv(filepath, nrows=1)
            lat = df["latitude"].iloc[0] if "latitude" in df.columns else np.nan
            lon = df["longitude"].iloc[0] if "longitude" in df.columns else np.nan
        coords[city] = (lat, lon)

    _CITY_COORDS_CACHE = coords
    return coords


def list_known_cities() -> list:
    """Returns the list of cities the models were trained on."""
    return sorted(_load_city_coordinates().keys())


def _build_feature_row(city: str, date: str, time: str,
                        latitude: float = None, longitude: float = None) -> pd.DataFrame:
    schema = _load_schema()

    ts = pd.Timestamp(f"{date} {time}")
    hour, day, month, day_of_week = ts.hour, ts.day, ts.month, ts.dayofweek

    if latitude is None or longitude is None:
        coords = _load_city_coordinates()
        if city not in coords:
            raise ValueError(
                f"City '{city}' not found in WeatherData/. Known cities: "
                f"{sorted(coords.keys())}. Pass latitude/longitude explicitly "
                "to predict for a new city."
            )
        latitude, longitude = coords[city]

    row = {
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week,
        "latitude": latitude,
        "longitude": longitude,
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "month_sin": np.sin(2 * np.pi * month / 12),
        "month_cos": np.cos(2 * np.pi * month / 12),
        "dow_sin": np.sin(2 * np.pi * day_of_week / 7),
        "dow_cos": np.cos(2 * np.pi * day_of_week / 7),
    }

    city_col_name = f"city_{city}"
    for col in schema["city_columns"]:
        row[col] = 1 if col == city_col_name else 0

    if city_col_name not in schema["city_columns"]:
        print(
            f"  [WARN] City '{city}' was not present in the training data. "
            "Prediction will rely only on latitude/longitude/time features "
            "(all city dummy columns set to 0), which may reduce accuracy."
        )

    feature_order = schema["base_feature_columns"] + schema["city_columns"]
    return pd.DataFrame([row])[feature_order]


def predict_weather(city: str, date: str, time: str = "12:00",
                     latitude: float = None, longitude: float = None,
                     rain_decision_threshold: float = 0.5) -> dict:
    """
    Predicts weather for a given city, date, and time.

    Parameters
    ----------
    city : str
        City name, e.g. "Bengaluru". Must match a city seen during training
        unless latitude/longitude are also provided. See list_known_cities().
    date : str
        Date string, e.g. "2026-07-15".
    time : str, default "12:00"
        Time string in 24-hour "HH:MM" format.
    latitude, longitude : float, optional
        Override coordinates. Required if `city` wasn't in the training data.
    rain_decision_threshold : float, default 0.5
        Probability above which rain is predicted "Yes".

    Returns
    -------
    dict with keys:
        temperature_2m (°C), shortwave_radiation (W/m²),
        rain_probability (0-1), rain_prediction ("Yes"/"No"),
        wind_speed_10m (km/h)
    """
    schema = _load_schema()
    X = _build_feature_row(city, date, time, latitude, longitude)

    result = {}

    for target in schema["regression_targets"]:
        model = _load_model(target)
        pred = model.predict(X)[0]
        if target in ("shortwave_radiation", "wind_speed_10m", "rain", "cloud_cover"):
            pred = max(0.0, pred)
        if target in ("relative_humidity_2m", "cloud_cover"):
            pred = min(100.0, pred)
        result[target] = round(float(pred), 2)

    return result


if __name__ == "__main__":
    cities = list_known_cities()
    print(f"Known cities: {cities}\n")

    sample_city = cities[0]
    result = predict_weather(city=sample_city, date="2026-07-15", time="13:00")
    print(f"Prediction for {sample_city} on 2026-07-15 at 13:00 ->")
    print(json.dumps(result, indent=2))

    night_result = predict_weather(city=sample_city, date="2026-12-25", time="02:00")
    print(f"\nPrediction for {sample_city} on 2026-12-25 at 02:00 ->")
    print(json.dumps(night_result, indent=2))
