"""Phase 3: EV energy consumption and battery prediction.

The model estimates route energy from vehicle, route, weather, and solar inputs.
It is deliberately transparent and configurable; it is an engineering estimate,
not a replacement for an OEM battery-management system or road-load test.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional

try:
    from config import (
        accessory_power_kw, air_density_kg_m3, drag_coefficient,
        drivetrain_efficiency, frontal_area_m2, regenerative_braking_efficiency,
        rolling_resistance_coefficient, temperature_penalty_per_c,
        temperature_reference_c,
    )
except ImportError:
    from .config import (
        accessory_power_kw, air_density_kg_m3, drag_coefficient,
        drivetrain_efficiency, frontal_area_m2, regenerative_braking_efficiency,
        rolling_resistance_coefficient, temperature_penalty_per_c,
        temperature_reference_c,
    )

GRAVITY_M_S2 = 9.80665


@dataclass(frozen=True)
class VehicleConfig:
    """Vehicle parameters used by the route-energy model."""

    rolling_resistance_coefficient: float = rolling_resistance_coefficient
    drag_coefficient: float = drag_coefficient
    frontal_area_m2: float = frontal_area_m2
    air_density_kg_m3: float = air_density_kg_m3
    drivetrain_efficiency: float = drivetrain_efficiency
    regenerative_braking_efficiency: float = regenerative_braking_efficiency
    accessory_power_kw: float = accessory_power_kw
    temperature_reference_c: float = temperature_reference_c
    temperature_penalty_per_c: float = temperature_penalty_per_c


def _positive(value: float, name: str, allow_zero: bool = True) -> float:
    value = float(value)
    if not isfinite(value) or value < 0 or (not allow_zero and value == 0):
        comparison = "zero or greater" if allow_zero else "greater than zero"
        raise ValueError(f"{name} must be a finite number {comparison}.")
    return value


def predict_ev_energy_consumption(
    vehicle_mass_kg: float,
    battery_capacity_kwh: float,
    route_distance_km: float,
    route_elevation_gain_m: float,
    speed_kmh: float,
    temperature_c: float,
    wind_speed_kmh: float,
    solar_energy_generated_kwh: float,
    initial_battery_percent: float = 100.0,
    route_elevation_loss_m: float = 0.0,
    vehicle_config: Optional[VehicleConfig] = None,
) -> dict:
    """Estimate route energy, remaining battery percentage, and remaining range.

    Wind speed is treated as a headwind, a conservative assumption when wind
    direction is unavailable. Elevation gain consumes energy; descent can return
    a configurable fraction through regenerative braking. Solar energy offsets
    the energy drawn from the battery but cannot charge beyond initial capacity.
    """
    mass = _positive(vehicle_mass_kg, "vehicle_mass_kg", allow_zero=False)
    capacity = _positive(battery_capacity_kwh, "battery_capacity_kwh", allow_zero=False)
    distance = _positive(route_distance_km, "route_distance_km")
    gain = _positive(route_elevation_gain_m, "route_elevation_gain_m")
    loss = _positive(route_elevation_loss_m, "route_elevation_loss_m")
    speed = _positive(speed_kmh, "speed_kmh")
    wind = _positive(wind_speed_kmh, "wind_speed_kmh")
    solar = _positive(solar_energy_generated_kwh, "solar_energy_generated_kwh")
    initial_soc = float(initial_battery_percent)
    if not 0 <= initial_soc <= 100:
        raise ValueError("initial_battery_percent must be between 0 and 100.")
    config = vehicle_config or VehicleConfig()
    if not 0 < config.drivetrain_efficiency <= 1:
        raise ValueError("drivetrain_efficiency must be greater than 0 and at most 1.")

    distance_m = distance * 1000
    travel_hours = distance / speed if speed else 0.0
    speed_m_s = speed / 3.6
    relative_air_speed_m_s = (speed + wind) / 3.6

    # Mechanical energy terms, converted from joules to kWh.
    rolling_resistance_kwh = (
        config.rolling_resistance_coefficient * mass * GRAVITY_M_S2 * distance_m / 3_600_000
    )
    aerodynamic_drag_kwh = (
        0.5 * config.air_density_kg_m3 * config.drag_coefficient * config.frontal_area_m2
        * relative_air_speed_m_s ** 2 * distance_m / 3_600_000
    )
    elevation_climb_kwh = mass * GRAVITY_M_S2 * gain / 3_600_000
    regenerative_energy_kwh = (
        mass * GRAVITY_M_S2 * loss / 3_600_000 * config.regenerative_braking_efficiency
    )

    propulsion_energy_kwh = (
        rolling_resistance_kwh + aerodynamic_drag_kwh + elevation_climb_kwh
    ) / config.drivetrain_efficiency - regenerative_energy_kwh
    # HVAC/battery-conditioning load rises above or below the comfort reference.
    temperature_load_factor = 1 + abs(float(temperature_c) - config.temperature_reference_c) * config.temperature_penalty_per_c
    accessory_energy_kwh = config.accessory_power_kw * travel_hours * temperature_load_factor
    gross_energy_consumed_kwh = max(0.0, propulsion_energy_kwh + accessory_energy_kwh)

    initial_energy_kwh = capacity * initial_soc / 100
    usable_solar_kwh = min(solar, max(0.0, capacity - initial_energy_kwh + gross_energy_consumed_kwh))
    net_battery_energy_used_kwh = max(0.0, gross_energy_consumed_kwh - usable_solar_kwh)
    # Solar above immediate route demand can charge available battery headroom.
    remaining_energy_kwh = min(
        capacity, max(0.0, initial_energy_kwh - gross_energy_consumed_kwh + usable_solar_kwh)
    )
    unmet_route_energy_kwh = max(0.0, net_battery_energy_used_kwh - initial_energy_kwh)
    remaining_battery_percent = remaining_energy_kwh / capacity * 100

    net_energy_per_km = net_battery_energy_used_kwh / distance if distance > 0 else 0.0
    remaining_range_km = remaining_energy_kwh / net_energy_per_km if net_energy_per_km > 0 else None

    return {
        "energy_consumed_kwh": round(net_battery_energy_used_kwh, 3),
        "gross_route_energy_kwh": round(gross_energy_consumed_kwh, 3),
        "solar_energy_generated_kwh": round(solar, 3),
        "solar_energy_used_kwh": round(usable_solar_kwh, 3),
        "battery_remaining_percent": round(remaining_battery_percent, 2),
        "battery_remaining_kwh": round(remaining_energy_kwh, 3),
        "unmet_route_energy_kwh": round(unmet_route_energy_kwh, 3),
        "estimated_remaining_range_km": round(remaining_range_km, 1) if remaining_range_km is not None else None,
        "route_distance_km": round(distance, 3),
        "travel_time_hours": round(travel_hours, 3),
        "net_energy_per_km_kwh": round(net_energy_per_km, 4),
        "temperature_load_factor": round(temperature_load_factor, 3),
        "energy_breakdown_kwh": {
            "rolling_resistance": round(rolling_resistance_kwh, 3),
            "aerodynamic_drag": round(aerodynamic_drag_kwh, 3),
            "elevation_climb": round(elevation_climb_kwh, 3),
            "regenerative_recovery": round(regenerative_energy_kwh, 3),
            "accessories_and_temperature": round(accessory_energy_kwh, 3),
        },
        "assumption": "Wind is treated as a headwind because direction is not supplied.",
    }
