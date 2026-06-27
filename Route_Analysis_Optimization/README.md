# Phase 4 — Solar-Assisted EV Route Analysis and Optimisation

Phase 4 independently evaluates every GPX file in the route folder, then ranks the routes using battery reserve, solar energy, travel time, and weather risk.

```text
GPX route → sampled points → weather prediction → solar prediction → EV energy prediction → scoring → best route
```

## Run

```powershell
cd "C:\Users\evang\Downloads\Project\Route_Analysis_Optimization"
python -m pip install -r requirements.txt
python run_route_analysis.py --departure-date 2026-06-25 --departure-time 08:00 --speed-kmh 55
```

The same run is available in `example_usage.py`.

The default input folder is `Route_dataset\kochi to bangalore`; every `.gpx` file is processed, including the supplied Route A, Route B, and Route C files. Use `--no-elevation-api` to disable Open-Elevation lookup when GPX files have no elevation.

## Processing

- GPX is parsed with the standard Python XML library—no GPX package is needed.
- Routes are sampled every 10 km and capped at 100 points, while always preserving start and end points.
- Arrival timestamps are calculated from departure date/time and estimated speed.
- Weather calls are cached by rounded location and hour. Existing weather-model fields are used where available; missing direct/diffuse/DNI fields are derived consistently from the available GHI/cloud result.
- Missing GPX elevation is looked up through Open-Elevation in batches; offline failures fall back safely to a flat/interpolated profile with a warning.
- The existing Phase 2 and Phase 3 functions are called without altering their solar or EV energy formulas.

## Score

All metrics are normalized so larger values are better:

```text
score = 0.50 × battery reserve
      + 0.25 × solar-energy advantage
      + 0.15 × travel-time advantage
      + 0.10 × weather safety
```

Weights and sampling limits are in `route_config.py`.

## Outputs

The `output/` folder receives one `<route>_results.csv` per GPX route, four per-route charts (battery, solar, elevation, weather risk), and:

- `route_comparison.csv`
- `route_comparison_bar_chart.png`
- `best_route.json`
- `route_summary.md`

The recommendation includes the winning route, reason, battery remaining, solar gain, travel time, and weather risk.
