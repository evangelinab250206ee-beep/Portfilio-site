# Interactive EV Route Optimisation Dashboard

## Start

```powershell
cd "C:\Users\evang\Downloads\Project\Route_Analysis_Optimization"
python -m pip install -r requirements.txt
streamlit run app.py
```

Enter city names, then select **Analyze Routes**. The dashboard geocodes both cities with OpenStreetMap Nominatim and requests up to three road-route alternatives from OSRM. If OSRM returns too few alternatives, it requests additional valid road routes through nearby midpoint detours.

Each route becomes a temporary GPX file and is passed unchanged through the existing Phase 1–4 modules. The dashboard only orchestrates those modules; it does not duplicate their weather, solar, EV, or scoring calculations.

## Current date and time

**Use Current Date & Time** is enabled by default. It uses the computer's local date and time at analysis, displays both values, and sends the selected departure time to the route optimizer. Disabling it exposes custom date/time inputs. Any input change—including departure time—automatically re-runs an existing analysis on the next Streamlit interaction.

## External services and fallbacks

City geocoding, road alternatives, and missing elevation use public OpenStreetMap/OSRM/Open-Elevation services, so internet access is required for a new city pair. Elevation API failures safely fall back to a flat/interpolated profile with a visible module warning. Existing weather-model failures use the established route-optimizer fallback and flag that status in `best_route.json`.

## Outputs

Each dashboard run creates a cached subfolder under `dashboard_runs/` containing temporary GPX routes, per-route results, the comparison CSV, recommendation JSON, Markdown report, charts, and `route_summary.pdf`.
