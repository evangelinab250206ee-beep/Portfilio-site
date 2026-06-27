"""Charging stop recommendation agent."""

from __future__ import annotations

from agents.base_agent import AgentProfile, BaseEVAgent
from config.settings import settings
from utils.geo import interpolate_path
from utils.types import ChargingPlan, ChargingStop, Location, RoutePlan


class ChargingAgent(BaseEVAgent):
    profile = AgentProfile(
        role="Charging Agent",
        goal="Decide whether charging is required and suggest practical stop locations.",
        backstory="A range anxiety reducer that keeps a usable battery buffer.",
    )

    def recommend(self, current_soc_pct: float, route: RoutePlan, remaining_range_km: float) -> ChargingPlan:
        buffer_km = max(20.0, route.distance_km * 0.12)
        if remaining_range_km >= route.distance_km + buffer_km and current_soc_pct > settings.charging_threshold_soc:
            return ChargingPlan(False, [], "No charging stop required for this route.")
        stop_fraction = min(0.82, max(0.35, remaining_range_km / max(route.distance_km, 1) * 0.72))
        candidate = interpolate_path(route.start, route.destination, 20)[int(stop_fraction * 19)]
        stop = ChargingStop(
            name="Recommended DC Fast Charger",
            location=Location(candidate.latitude, candidate.longitude, "charging-stop"),
            distance_from_start_km=route.distance_km * stop_fraction,
            recommended_charge_to_pct=82.0,
        )
        return ChargingPlan(True, [stop], "Charge recommended to preserve arrival buffer.")
