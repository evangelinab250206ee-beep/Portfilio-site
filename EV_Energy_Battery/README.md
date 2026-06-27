# Phase 3 — EV Energy Consumption and Battery Prediction

This module consumes the per-point CSV produced by Phase 2 and predicts EV energy use, battery state, and range along the route.

```text
weather_predictions.csv
        ↓
Solar_EV_Energy / solar_ev_predictor.py
        ↓
solar_ev_results.csv
        ↓
EV_Energy_Battery / ev_energy_predictor.py
        ↓
ev_energy_results.csv + charts + summary
```

## Install and run

```powershell
cd "C:\Users\evang\Downloads\Project\EV_Energy_Battery"
python -m pip install -r requirements.txt
python run_ev_pipeline.py
```

To choose a solar-result file or override the default vehicle mass, capacity, and initial charge:

```powershell
python run_ev_pipeline.py "C:\path\to\solar_ev_results.csv" --vehicle-mass-kg 1500 --battery-capacity-kwh 60 --initial-battery-percent 90
```

## Required Phase 2 columns

`solar_ev_results.csv` must contain:

```text
timestamp, distance_km, vehicle_speed_kmh, solar_energy_wh,
ambient_temperature_c, wind_speed_kmh
```

For elevation energy, add `elevation_m` to the route/solar results before Phase 3. The module derives the positive elevation gain between consecutive points. If the column is absent, it warns and runs with a flat route so the pipeline remains usable.

## Default vehicle configuration

| Parameter | Default |
|---|---:|
| Vehicle mass | 1500 kg |
| Battery capacity | 60 kWh |
| Drag coefficient | 0.24 |
| Frontal area | 2.2 m² |
| Rolling resistance coefficient | 0.010 |
| Drivetrain efficiency | 0.90 |

Change these values in [vehicle_config.py](vehicle_config.py) or construct `VehicleConfig` in Python.

## Calculations

- Rolling-resistance force: `m × g × Crr`
- Aerodynamic-drag force: `0.5 × rho × Cd × A × relative_air_speed²`
- Elevation energy: `m × g × positive_elevation_gain`
- Energy terms are divided by drivetrain efficiency and adjusted by a small ambient-temperature factor.
- Net energy consumption is `energy_consumed_wh − solar_energy_wh`.
- Battery remaining is applied cumulatively at every route point and is constrained to 0–100%.
- Remaining range uses cumulative net Wh/km and the current battery energy.

Wind direction is not available, so wind speed is treated as a headwind. Missing numeric values are timestamp-interpolated then median-filled. Only required CSV columns are read, numeric data uses `float32`, and NumPy vector calculations support thousands of points.

## Outputs

The configured output folder contains:

- `ev_energy_results.csv` — one row per route point with distance, elevation, speed, consumed energy, solar energy, net energy, battery percentage, and range
- `ev_energy_summary.md`
- `battery_remaining_vs_distance.png`
- `energy_consumption_vs_distance.png`
- `elevation_vs_distance.png`
- `solar_energy_vs_distance.png`
- `remaining_range_vs_distance.png`

## Python API

```python
from ev_energy_predictor import load_solar_results, predict_trip_energy, save_results

route_points = load_solar_results("../Solar_EV_Energy/output/solar_ev_results.csv")
results, summary = predict_trip_energy(route_points)
save_results(results, summary, "output")
```

Route optimisation is intentionally not included.
