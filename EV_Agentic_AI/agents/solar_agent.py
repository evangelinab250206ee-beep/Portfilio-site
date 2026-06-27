"""Solar prediction agent using NASA POWER, ML, or clear-sky heuristics."""

from __future__ import annotations

from datetime import datetime

import numpy as np

from agents.base_agent import AgentProfile, BaseEVAgent
from database.db import EVDatabase
from models.model_manager import ModelManager
from utils.types import Location, SolarPrediction


class SolarAgent(BaseEVAgent):
    profile = AgentProfile(
        role="Solar Agent",
        goal="Estimate available solar radiation and EV auxiliary solar gain.",
        backstory="A solar forecasting agent combining satellite data and local weather context.",
    )

    def __init__(self, db: EVDatabase | None = None, model_manager: ModelManager | None = None, panel_area_m2: float = 2.2, efficiency: float = 0.21) -> None:
        self.db = db
        self.model_manager = model_manager or ModelManager()
        self.panel_area_m2 = panel_area_m2
        self.efficiency = efficiency

    def predict(self, location: Location, when: datetime, cloud_cover_pct: float) -> SolarPrediction:
        prediction = self._from_nasa_power(location, when, cloud_cover_pct) or self._from_model_or_heuristic(location, when, cloud_cover_pct)
        if self.db:
            self.db.log_solar(location.latitude, location.longitude, prediction)
        return prediction

    def _from_nasa_power(self, location: Location, when: datetime, cloud_cover_pct: float) -> SolarPrediction | None:
        try:
            import requests

            day = when.strftime("%Y%m%d")
            response = requests.get(
                "https://power.larc.nasa.gov/api/temporal/daily/point",
                params={
                    "parameters": "ALLSKY_SFC_SW_DWN",
                    "community": "RE",
                    "longitude": location.longitude,
                    "latitude": location.latitude,
                    "start": day,
                    "end": day,
                    "format": "JSON",
                },
                timeout=8,
            )
            response.raise_for_status()
            daily_kwh_m2 = response.json()["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"][day]
            daylight_factor = max(0.0, np.sin((when.hour - 6) / 12 * np.pi))
            irradiance = max(0.0, daily_kwh_m2 * 1000 / 6 * daylight_factor * (1 - 0.004 * cloud_cover_pct))
            return self._format(irradiance, "nasa_power")
        except Exception:
            return None

    def _from_model_or_heuristic(self, location: Location, when: datetime, cloud_cover_pct: float) -> SolarPrediction:
        model = self.model_manager.load_sklearn("solar_random_forest")
        features = np.array([[location.latitude, location.longitude, when.month, when.hour, cloud_cover_pct]])
        if model is not None:
            return self._format(float(model.predict(features)[0]), "solar_random_forest")
        daylight = max(0.0, np.sin((when.hour - 6) / 12 * np.pi))
        season = 0.82 + 0.18 * np.sin((when.month - 2) / 12 * 2 * np.pi)
        irradiance = max(0.0, 980 * daylight * season * (1 - 0.0075 * cloud_cover_pct))
        return self._format(irradiance, "heuristic")

    def _format(self, irradiance_w_m2: float, source: str) -> SolarPrediction:
        power_kw = irradiance_w_m2 * self.panel_area_m2 * self.efficiency / 1000
        return SolarPrediction(float(irradiance_w_m2), float(power_kw), source)
