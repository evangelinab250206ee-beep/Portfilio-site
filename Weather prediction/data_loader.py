"""
data_loader.py
-----------------
Loads every city CSV from WeatherData/, cleans and standardizes columns,
merges into one DataFrame, and adds time features.

Expected raw file format (standard Open-Meteo hourly export):

    latitude,longitude,elevation,utc_offset_seconds,timezone,timezone_abbreviation
    12.9716,77.5946,920.0,19800,Asia/Kolkata,GMT+5:30
    <blank line>
    time,temperature_2m (°C),relative_humidity_2m (%),precipitation (mm),
        wind_speed_10m (km/h),shortwave_radiation (W/m²),direct_radiation (W/m²),
        cloud_cover (%),surface_pressure (hPa),diffuse_radiation (W/m²),
        direct_normal_irradiance (W/m²),wind_direction_10m (°),rain (mm)
    2025-06-01T00:00,25.8,93,0.40,10.6,0.0,0.0,98,1010.0,0.0,0.0,316,0.40
    ...

latitude/longitude live in the metadata block (not repeated per row in the
raw file) and are broadcast onto every hourly row of that city by this loader.
"""

import os
import glob
import re
import numpy as np
import pandas as pd

# Regex patterns matched (case-insensitive) against raw headers to strip
# units and standardize names, e.g. 'temperature_2m (°C)' -> 'temperature_2m'.
COLUMN_RENAME_PATTERNS = {
    r"^time$": "time",
    r"^temperature_2m": "temperature_2m",
    r"^relative_humidity_2m": "relative_humidity_2m",
    r"^precipitation": "precipitation",
    r"^wind_speed_10m": "wind_speed_10m",
    r"^wind_direction_10m": "wind_direction_10m",
    r"^shortwave_radiation": "shortwave_radiation",
    r"^direct_radiation": "direct_radiation",
    r"^diffuse_radiation": "diffuse_radiation",
    r"^direct_normal_irradiance": "direct_normal_irradiance",
    r"^cloud_cover": "cloud_cover",
    r"^surface_pressure": "surface_pressure",
    r"^rain": "rain",
}

# Columns this project's models use downstream. If a file is missing one,
# it's filled with NaN and cleaned later.
REQUIRED_COLUMNS = [
    "time",
    "temperature_2m",
    "relative_humidity_2m",
    "rain",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
    "shortwave_radiation",
    "latitude",
    "longitude",
]

NUMERIC_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "rain",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
    "shortwave_radiation",
    "latitude",
    "longitude",
]


def city_name_from_filename(filepath: str) -> str:
    """
    Derives a clean city name from a filename like:
      'Bengaluru_weatherData.csv' -> 'Bengaluru'
      'new-york_weather_data.csv' -> 'New York'
    """
    base = os.path.basename(filepath)
    name = os.path.splitext(base)[0]

    noise_tokens = [
        "open_meteo", "open-meteo", "openmeteo",
        "weatherdata", "weather_data", "weather-data",
        "weather", "data", "hourly", "export",
    ]
    name_lower = name.lower()
    for token in noise_tokens:
        name_lower = name_lower.replace(token, "")

    name_clean = re.sub(r"[_\-]+", " ", name_lower).strip()
    name_clean = re.sub(r"\s+", " ", name_clean)

    if not name_clean:
        name_clean = name

    return name_clean.title()


def _standardize_columns(columns) -> dict:
    rename_map = {}
    for raw_col in columns:
        raw_stripped = raw_col.strip()
        for pattern, clean_name in COLUMN_RENAME_PATTERNS.items():
            if re.match(pattern, raw_stripped, flags=re.IGNORECASE):
                rename_map[raw_col] = clean_name
                break
    return rename_map


def load_single_csv(filepath: str) -> pd.DataFrame:
    """
    Loads one city's Open-Meteo CSV export. Auto-detects:
      1. Standard Open-Meteo layout: 2-row metadata block + blank line +
         hourly table (lat/lon broadcast from metadata onto every row).
      2. Flat CSV with 'time' as the first column and lat/lon as normal
         per-row columns.
    """
    with open(filepath, "r", encoding="utf-8") as fh:
        first_line = fh.readline().strip().lower()

    latitude, longitude = np.nan, np.nan

    if first_line.startswith("latitude"):
        meta = pd.read_csv(filepath, nrows=1)
        if "latitude" in meta.columns:
            latitude = meta["latitude"].iloc[0]
        if "longitude" in meta.columns:
            longitude = meta["longitude"].iloc[0]

        df = pd.read_csv(filepath, skiprows=3)
        df["latitude"] = latitude
        df["longitude"] = longitude
    else:
        df = pd.read_csv(filepath)

    rename_map = _standardize_columns(df.columns)
    df = df.rename(columns=rename_map)

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        print(
            f"  [WARN] {os.path.basename(filepath)} is missing columns "
            f"{missing_cols}. They will be filled with NaN."
        )
        for c in missing_cols:
            df[c] = np.nan

    df["city"] = city_name_from_filename(filepath)
    return df[REQUIRED_COLUMNS + ["city"]]


def load_all_csvs(folder_path: str) -> pd.DataFrame:
    """Reads every .csv in `folder_path`, tags with city, concatenates."""
    csv_files = sorted(glob.glob(os.path.join(folder_path, "*.csv")))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in '{folder_path}'. "
            "Make sure WeatherData/ contains the Open-Meteo exports."
        )

    print(f"Found {len(csv_files)} CSV file(s) in '{folder_path}':")
    frames = []
    for f in csv_files:
        print(f"  - Loading {os.path.basename(f)}")
        frames.append(load_single_csv(f))

    merged = pd.concat(frames, ignore_index=True)
    print(f"Merged dataset shape: {merged.shape}")
    return merged


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans missing values:
      - Parses 'time' to datetime, drops unparsable rows.
      - Numeric columns: linear interpolation per-city along time,
        then per-city median, then global median as a last resort.
      - Clips physically-impossible values (no negative rain/wind/etc).
    """
    df = df.copy()

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    n_before = len(df)
    df = df.dropna(subset=["time"])
    if n_before != len(df):
        print(f"  Dropped {n_before - len(df)} rows with unparsable 'time' values.")

    df = df.sort_values(["city", "time"]).reset_index(drop=True)

    # de-duplicate exact (city, time) repeats if any
    n_before_dedup = len(df)
    df = df.drop_duplicates(subset=["city", "time"], keep="first")
    if n_before_dedup != len(df):
        print(f"  Dropped {n_before_dedup - len(df)} duplicate (city, time) rows.")

    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df.groupby("city")[col].transform(
            lambda s: s.interpolate(method="linear", limit_direction="both")
        )
        df[col] = df.groupby("city")[col].transform(lambda s: s.fillna(s.median()))
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())

    for col in ["rain", "wind_speed_10m", "shortwave_radiation", "surface_pressure",
                "relative_humidity_2m"]:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)
    if "relative_humidity_2m" in df.columns:
        df["relative_humidity_2m"] = df["relative_humidity_2m"].clip(upper=100)
    if "wind_direction_10m" in df.columns:
        df["wind_direction_10m"] = df["wind_direction_10m"] % 360

    remaining = df.isna().sum()
    remaining = remaining[remaining > 0]
    if len(remaining):
        print(f"Missing values remaining after cleaning:\n{remaining}")
    else:
        print("No missing values remain after cleaning.")
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds hour, day, month, day_of_week (+ year, kept for completeness)."""
    df = df.copy()
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["day"] = df["time"].dt.day
    df["hour"] = df["time"].dt.hour
    df["day_of_week"] = df["time"].dt.dayofweek  # Monday=0 ... Sunday=6
    return df


def add_rain_label(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    """Adds a binary 'rain_flag' target: 1 if rain (mm) exceeds threshold."""
    df = df.copy()
    df["rain_flag"] = (df["rain"] > threshold).astype(int)
    return df


def build_dataset(folder_path: str, rain_threshold: float = 0.1) -> pd.DataFrame:
    """Full pipeline: load -> merge -> clean -> time features -> rain label."""
    df = load_all_csvs(folder_path)
    df = handle_missing_values(df)
    df = add_time_features(df)
    df = add_rain_label(df, threshold=rain_threshold)
    return df


if __name__ == "__main__":
    data = build_dataset("WeatherData")
    print(data.head())
    print(data["city"].value_counts())
    print("Rain class balance:\n", data["rain_flag"].value_counts(normalize=True))
