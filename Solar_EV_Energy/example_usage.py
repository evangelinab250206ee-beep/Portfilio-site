"""Run a CSV-driven weather prediction to solar-energy pipeline."""
from pathlib import Path

from solar_ev_predictor import load_weather_predictions, predict_trip_solar_energy, save_results

weather_points = load_weather_predictions("weather_predictions.csv")
weather_points["vehicle_speed_kmh"] = 50  # Route module can supply this later.
results, summary = predict_trip_solar_energy(weather_points, trip_energy_demand_kwh=8.0)
saved = save_results(results, summary, Path("output"))
print(results[["timestamp", "net_solar_power_w", "solar_energy_wh"]].to_string(index=False))
print("\nSummary:", summary)
print("Saved:", saved)
