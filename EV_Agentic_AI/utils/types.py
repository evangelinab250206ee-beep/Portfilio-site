"""Shared data contracts used by agents, dashboard, and tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    label: str = ""


@dataclass(frozen=True)
class SensorReading:
    timestamp: datetime
    location: Location
    temperature_c: float
    humidity_pct: float
    battery_voltage_v: float
    battery_current_a: float
    vehicle_speed_kmh: float
    battery_soc_pct: float


@dataclass(frozen=True)
class WeatherPrediction:
    temperature_c: float
    humidity_pct: float
    rain_probability_pct: float
    wind_speed_mps: float
    cloud_cover_pct: float
    source: str = "heuristic"


@dataclass(frozen=True)
class SolarPrediction:
    irradiance_w_m2: float
    solar_power_kw: float
    source: str = "heuristic"


@dataclass(frozen=True)
class EnergyPrediction:
    consumption_kwh_per_100km: float
    remaining_range_km: float
    energy_required_kwh: float = 0.0
    source: str = "heuristic"


@dataclass(frozen=True)
class RouteStep:
    instruction: str
    distance_km: float
    duration_min: float
    location: Location


@dataclass(frozen=True)
class TrafficSegment:
    start: Location
    end: Location
    status: str
    distance_km: float
    duration_min: float
    path: list[Location] = field(default_factory=list)


@dataclass(frozen=True)
class RouteWaypoint:
    name: str
    location: Location
    eta_min: float
    weather: str = ""
    solar_score: str = ""


@dataclass(frozen=True)
class RoutePlan:
    start: Location
    destination: Location
    distance_km: float
    travel_time_min: float
    path: list[Location]
    energy_required_kwh: float
    source: str = "geodesic"
    route_name: str = "Recommended Route"
    steps: list[RouteStep] = field(default_factory=list)
    traffic_segments: list[TrafficSegment] = field(default_factory=list)
    waypoints: list[RouteWaypoint] = field(default_factory=list)
    road_names: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChargingStop:
    name: str
    location: Location
    distance_from_start_km: float
    recommended_charge_to_pct: float


@dataclass(frozen=True)
class ChargingPlan:
    required: bool
    stops: list[ChargingStop] = field(default_factory=list)
    message: str = ""


@dataclass(frozen=True)
class DecisionSummary:
    route: RoutePlan
    weather: WeatherPrediction
    solar: SolarPrediction
    energy: EnergyPrediction
    charging: ChargingPlan
    weather_risk: str
    estimated_battery_remaining_pct: float
    route_alternatives: list[RoutePlan] = field(default_factory=list)
