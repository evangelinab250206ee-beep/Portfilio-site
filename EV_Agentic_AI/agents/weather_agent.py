"""Weather agent using OpenWeatherMap, trained models, or heuristics."""

from __future__ import annotations

from datetime import datetime

import numpy as np

from agents.base_agent import AgentProfile, BaseEVAgent
from config.settings import settings
from database.db import EVDatabase
from models.model_manager import ModelManager
from utils.types import Location, WeatherPrediction


class WeatherAgent(BaseEVAgent):
    profile = AgentProfile(
        role="Weather Agent",
        goal="Predict weather hazards that affect EV range and routing.",
        backstory="A meteorology-focused EV route planning specialist.",
    )

    def __init__(self, db: EVDatabase | None = None, model_manager: ModelManager | None = None) -> None:
        self.db = db
        self.model_manager = model_manager or ModelManager()

    def predict(self, location: Location, when: datetime) -> WeatherPrediction:
        api_prediction = self._from_openweather(location)
        if api_prediction:
            prediction = api_prediction
        else:
            prediction = self._from_model_or_heuristic(location, when)
        if self.db:
            self.db.log_weather(location.latitude, location.longitude, prediction)
        return prediction

    def _from_openweather(self, location: Location) -> WeatherPrediction | None:
        if not settings.openweather_api_key:
            return None
        try:
            import requests

            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "appid": settings.openweather_api_key,
                    "units": "metric",
                },
                timeout=8,
            )
            response.raise_for_status()
            data = response.json()
            clouds = float(data.get("clouds", {}).get("all", 0))
            rain_probability = min(100.0, clouds * 0.75 + (20 if "rain" in data else 0))
            return WeatherPrediction(
                temperature_c=float(data["main"]["temp"]),
                humidity_pct=float(data["main"]["humidity"]),
                rain_probability_pct=rain_probability,
                wind_speed_mps=float(data.get("wind", {}).get("speed", 0)),
                cloud_cover_pct=clouds,
                source="openweathermap",
            )
        except Exception:
            return None

    def _from_model_or_heuristic(self, location: Location, when: datetime) -> WeatherPrediction:
        model = self.model_manager.load_sklearn("weather_random_forest")
        features = np.array([[location.latitude, location.longitude, when.month, when.hour]])
        if model is not None:
            temp, humidity, wind, cloud, rain = model.predict(features)[0]
            return WeatherPrediction(float(temp), float(humidity), float(rain), float(wind), float(cloud), "weather_random_forest")
        daylight = max(0.0, np.sin((when.hour - 6) / 12 * np.pi))
        temp = 22 + 10 * daylight + 3 * np.sin((when.month - 2) / 12 * 2 * np.pi)
        humidity = 62 + 12 * (1 - daylight)
        cloud = 35 + 20 * (humidity / 100)
        rain = min(100.0, cloud * 0.55)
        return WeatherPrediction(float(temp), float(humidity), float(rain), 3.2, float(cloud), "heuristic")
