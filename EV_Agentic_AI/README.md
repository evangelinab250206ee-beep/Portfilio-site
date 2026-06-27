# EV Agentic AI

Python-based agentic AI platform for Electric Vehicle smart route planning, energy prediction, weather awareness, solar radiation estimation, and charging recommendations.

## What Is Included

- Consumer-focused Streamlit dashboard for location search, SOC, range, weather, Folium route map, route intelligence, and charging suggestions.
- SQLite database for sensor logs, route history, weather history, energy predictions, and solar predictions.
- Agentic architecture with Weather, Solar, Energy, Route, Charging, and Decision agents.
- Machine-learning training scripts for weather, solar, and energy consumption models.
- OpenWeatherMap and NASA POWER integration with offline heuristic fallbacks.
- OSRM road routing with turn instructions, OSMnx/NetworkX fallback, and geodesic fallback.
- ESP32/Arduino serial sensor parser and reader.
- Unit tests for agents, database, and sensor parsing.

## Project Phases

1. Project structure, database, and dashboard.
2. Weather Agent using OpenWeatherMap, Random Forest/XGBoost training, and fallback prediction.
3. Solar Agent using NASA POWER, Random Forest/LSTM training, and cloud-aware prediction.
4. Energy Agent using Gradient Boosting/Neural Network training and range estimation.
5. Route Agent using OSMnx/NetworkX when available.
6. Charging Agent for route-aware charging recommendations.
7. Decision Agent to coordinate all agents.
8. Integration tests and command-line verification.

## Setup

```powershell
cd C:\Users\evang\Downloads\Project\EV_Agentic_AI
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt
```

Set optional API and hardware configuration:

```powershell
$env:OPENWEATHER_API_KEY="your_openweather_key"
$env:EV_SERIAL_PORT="COM3"
$env:EV_SERIAL_BAUDRATE="115200"
```

## Run

Command-line decision:

```powershell
python main.py --start-lat 12.9716 --start-lon 77.5946 --dest-lat 13.0358 --dest-lon 77.5970 --soc 75
```

Streamlit dashboard:

```powershell
python -m streamlit run dashboard/app.py
```

The dashboard uses OpenStreetMap Nominatim for place search. If the network is unavailable, it falls back to configured default coordinates.

Route intelligence includes:

- Real road geometry from OSRM when internet access is available.
- Colored traffic segments using route speed and weather-aware scoring.
- Weather and solar markers along the route.
- EV charging station layer with provider, availability, speed, cost, and distance estimates.
- Route comparison for fastest, efficient, and weather-safe options.
- Turn-by-turn navigation, route timeline, live re-routing advisor, and risk score.

Install optional route/agent/deep-learning packages after the core app is running:

```powershell
python -m pip install -r requirements-optional.txt
```

## Train Models

The training scripts work with synthetic data by default, or with CSV files matching the documented columns in each script.

```powershell
python -m models.train_weather
python -m models.train_solar
python -m models.train_energy
```

Model artifacts are saved in `models/artifacts/`.

## Sensor Input

JSON line format:

```json
{"lat":12.97,"lon":77.59,"temperature":30,"humidity":60,"voltage":360,"current":18,"speed":42,"soc":71}
```

CSV line format:

```text
lat,lon,temperature,humidity,voltage,current,speed,soc
```

Example:

```text
12.97,77.59,30,60,360,18,42,71
```

## Tests

```powershell
python -m unittest discover -s tests -v
```

If pytest is installed:

```powershell
pytest -q
```

## Notes

- Without API keys, the system uses deterministic fallback predictors so development can continue offline.
- OSMnx may require network access to download OpenStreetMap data. If unavailable, the Route Agent uses a distance-adjusted geodesic route.
- CrewAI is represented through agent profiles and optional CrewAI wrappers. The deterministic agent tools run without CrewAI installed, while the project remains ready for Crew/task orchestration.
