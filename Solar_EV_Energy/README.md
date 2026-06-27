# Phase 2 — Solar-Assisted EV Energy Prediction

This module converts Weather Prediction System output directly into EV roof-solar generation. It estimates solar energy only; it does **not** calculate battery depletion, state of charge, or traction consumption.

## Automated pipeline

```text
weather_predictions.csv
        ↓
load_weather_predictions()
        ↓
predict_trip_solar_energy()
        ↓
solar_ev_results.csv + summary report + PNG graphs
```

## Run

```powershell
cd "C:\Users\evang\Downloads\Project\Solar_EV_Energy"
python -m pip install -r requirements.txt
python run_pipeline.py
```

`run_pipeline.py` uses the included `weather_predictions.csv` by default. To use a Weather Prediction System export or choose a route speed, run:

```powershell
python run_pipeline.py "C:\path\to\weather_predictions.csv" --vehicle-speed-kmh 55 --output-dir output
```

Optionally provide an external trip-energy estimate solely to calculate the solar contribution percentage:

```powershell
python run_pipeline.py weather_predictions.csv --trip-energy-demand-kwh 8.0
```

Generated files are `solar_ev_results.csv`, `solar_ev_summary.md`, `solar_power_vs_time.png`, `solar_energy_vs_time.png`, `ghi_vs_time.png`, `cloud_cover_vs_solar_output.png`, and `temperature_vs_solar_efficiency.png`.

## Required Weather Prediction CSV columns

```text
timestamp, latitude, longitude, temperature_2m, precipitation,
wind_speed_10m, cloud_cover, shortwave_radiation, direct_radiation,
diffuse_radiation, direct_normal_irradiance
```

The loader maps the weather names automatically:

| Weather CSV | Solar module input |
|---|---|
| `temperature_2m` | `temperature` |
| `wind_speed_10m` | `wind_speed` |
| `shortwave_radiation` | `predicted_ghi` |
| `direct_radiation` | `predicted_direct_radiation` |
| `diffuse_radiation` | `predicted_dhi` |
| `direct_normal_irradiance` | `predicted_dni` |

`precipitation` is retained in the output for traceability but does not alter the current solar formula. `vehicle_speed_kmh` is optional: add it to the CSV or pass `--vehicle-speed-kmh`. Timestamp intervals automatically become `duration_hours`; the final point uses the last valid interval (or one hour when only one point exists).

## Validation and scaling

`load_weather_predictions(csv_file_path)` validates the required headers, drops invalid timestamps with warnings, interpolates missing numeric values by time, then fills remaining values with the column median. It warns about invalid cloud, radiation, wind, and coordinate values; the established solar calculation clamps irradiance and cloud cover where applicable.

Only columns required by the solar pipeline are read from CSV, numeric values are stored as `float32`, and the DataFrame is processed using `itertuples`. This keeps memory use practical for thousands of route points.

## Existing API remains available

The established functions remain unchanged for existing callers:

```python
from solar_ev_predictor import predict_solar_power, predict_hourly_solar_energy, predict_trip_solar_energy
```

They still accept an iterable of manually prepared records. The new loader returns a DataFrame that can be passed directly to `predict_trip_solar_energy()`.

## Structure

```text
Solar_EV_Energy/
├── solar_ev_predictor.py   # calculations plus CSV loader
├── run_pipeline.py         # automated command-line pipeline
├── weather_predictions.csv # example Weather Prediction System output
├── config.py               # panel settings
├── example_usage.py
├── requirements.txt
└── output/                 # generated results
```
