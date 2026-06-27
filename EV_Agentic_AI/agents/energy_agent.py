"""EV battery energy consumption and remaining range agent."""

from __future__ import annotations

import numpy as np

from agents.base_agent import AgentProfile, BaseEVAgent
from config.settings import settings
from database.db import EVDatabase
from models.model_manager import ModelManager
from utils.types import EnergyPrediction


class EnergyAgent(BaseEVAgent):
    profile = AgentProfile(
        role="Energy Agent",
        goal="Estimate energy use and remaining range from vehicle and environment conditions.",
        backstory="A drivetrain efficiency specialist for battery electric vehicles.",
    )

    def __init__(self, db: EVDatabase | None = None, model_manager: ModelManager | None = None) -> None:
        self.db = db
        self.model_manager = model_manager or ModelManager()

    def predict(
        self,
        vehicle_speed_kmh: float,
        battery_soc_pct: float,
        road_gradient_pct: float,
        temperature_c: float,
        route_distance_km: float = 0.0,
    ) -> EnergyPrediction:
        model = self.model_manager.load_sklearn("energy_gradient_boosting")
        features = np.array([[vehicle_speed_kmh, battery_soc_pct, road_gradient_pct, temperature_c]])
        if model is not None:
            consumption = float(model.predict(features)[0])
            source = "energy_gradient_boosting"
        else:
            temp_penalty = abs(temperature_c - 22) * 0.12
            aero = 0.0016 * vehicle_speed_kmh**2
            hill = max(road_gradient_pct, 0) * 0.75 + min(road_gradient_pct, 0) * 0.22
            consumption = max(7.0, 10.5 + aero + hill + temp_penalty)
            source = "heuristic"
        available_kwh = settings.usable_battery_kwh * max(0, min(100, battery_soc_pct)) / 100
        remaining_range = available_kwh / consumption * 100
        energy_required = route_distance_km * consumption / 100
        prediction = EnergyPrediction(float(consumption), float(remaining_range), float(energy_required), source)
        if self.db:
            self.db.log_energy(prediction)
        return prediction
