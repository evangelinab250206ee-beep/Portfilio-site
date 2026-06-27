"""Decision agent that coordinates all specialist agents."""

from __future__ import annotations

from datetime import datetime

from agents.base_agent import AgentProfile, BaseEVAgent
from agents.charging_agent import ChargingAgent
from agents.energy_agent import EnergyAgent
from agents.route_agent import RouteAgent
from agents.solar_agent import SolarAgent
from agents.weather_agent import WeatherAgent
from config.settings import settings
from database.db import EVDatabase
from utils.types import DecisionSummary, Location


class DecisionAgent(BaseEVAgent):
    profile = AgentProfile(
        role="Decision Agent",
        goal="Combine agent outputs into one EV route and energy decision.",
        backstory="A coordinator that weighs range, weather, solar gain, charging, and route tradeoffs.",
    )

    def __init__(self, db: EVDatabase | None = None) -> None:
        self.db = db or EVDatabase()
        self.weather_agent = WeatherAgent(self.db)
        self.solar_agent = SolarAgent(self.db)
        self.energy_agent = EnergyAgent(self.db)
        self.route_agent = RouteAgent(self.db)
        self.charging_agent = ChargingAgent()

    def decide(
        self,
        start: Location,
        destination: Location,
        current_soc_pct: float = settings.default_soc,
        vehicle_speed_kmh: float = 55.0,
        road_gradient_pct: float = 1.0,
        when: datetime | None = None,
    ) -> DecisionSummary:
        when = when or datetime.now()
        weather = self.weather_agent.predict(start, when)
        solar = self.solar_agent.predict(start, when, weather.cloud_cover_pct)
        initial_energy = self.energy_agent.predict(vehicle_speed_kmh, current_soc_pct, road_gradient_pct, weather.temperature_c)
        route_alternatives = self.route_agent.plan_alternatives(start, destination, weather, initial_energy.consumption_kwh_per_100km)
        route = route_alternatives[0]
        energy = self.energy_agent.predict(vehicle_speed_kmh, current_soc_pct, road_gradient_pct, weather.temperature_c, route.distance_km)
        charging = self.charging_agent.recommend(current_soc_pct, route, energy.remaining_range_km)
        battery_used_pct = energy.energy_required_kwh / settings.usable_battery_kwh * 100
        battery_remaining = max(0.0, current_soc_pct - battery_used_pct)
        risk = self._weather_risk(weather.rain_probability_pct, weather.wind_speed_mps)
        return DecisionSummary(route, weather, solar, energy, charging, risk, float(battery_remaining), route_alternatives)

    @staticmethod
    def _weather_risk(rain_probability_pct: float, wind_speed_mps: float) -> str:
        if rain_probability_pct >= 70 or wind_speed_mps >= 12:
            return "High"
        if rain_probability_pct >= 40 or wind_speed_mps >= 8:
            return "Moderate"
        return "Low"
