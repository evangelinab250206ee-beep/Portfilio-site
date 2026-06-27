"""Consumer-focused Streamlit dashboard for the EV Agentic AI platform."""

from __future__ import annotations

from dataclasses import dataclass, replace
from html import escape
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.decision_agent import DecisionAgent
from config.settings import settings
from database.db import EVDatabase
from utils.geocoding import configured_current_location, geocode_place
from utils.types import DecisionSummary, Location


@dataclass(frozen=True)
class ChargingStationView:
    name: str
    location: Location
    distance_km: float
    availability: str
    speed_kw: int
    cost_per_kwh: int


SOLAR_ROOF_AREA_M2 = 2.5
SOLAR_PANEL_EFFICIENCY = 0.22
KWH_PER_KM = 0.16
SOLAR_PLANNING_WINDOW_H = 4.0


@st.cache_data(ttl=3600, show_spinner=False)
def cached_geocode(query: str, limit: int = 8) -> list[tuple[float, float, str]]:
    return [(result.location.latitude, result.location.longitude, result.display_name) for result in geocode_place(query, limit)]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ev-green: #19a974;
            --ev-orange: #f59e0b;
            --ev-red: #dc2626;
            --ev-blue: #2563eb;
            --ev-card: rgba(255,255,255,.86);
            --ev-border: rgba(120,120,120,.20);
            --ev-muted: rgba(90,90,90,.78);
            --ev-shadow: 0 10px 28px rgba(15, 23, 42, .08);
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --ev-card: rgba(24,28,35,.88);
                --ev-border: rgba(255,255,255,.12);
                --ev-muted: rgba(220,220,220,.72);
                --ev-shadow: 0 10px 28px rgba(0,0,0,.30);
            }
        }
        .block-container {padding-top: 1.2rem; max-width: 1180px;}
        h1, h2, h3 {letter-spacing: 0;}
        [data-testid="stSidebar"] {border-right: 1px solid var(--ev-border);}
        .ev-hero, .ev-card, .ev-kpi, .ev-route-card, .ev-insights {
            background: var(--ev-card);
            border: 1px solid var(--ev-border);
            border-radius: 8px;
            box-shadow: var(--ev-shadow);
        }
        .ev-hero {padding: 22px; margin: 8px 0 18px;}
        .ev-title-row {display:flex; justify-content:space-between; gap:14px; align-items:flex-start;}
        .ev-hero h1 {font-size: 1.65rem; margin: 0 0 8px;}
        .ev-subtle {color: var(--ev-muted); font-size: .92rem;}
        .ev-hero-grid {display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:14px; margin-top:16px;}
        .ev-pill {display:inline-flex; align-items:center; gap:6px; padding:6px 10px; border-radius:999px; font-weight:700; font-size:.86rem;}
        .ev-pill.green {background: rgba(25,169,116,.14); color: var(--ev-green);}
        .ev-pill.orange {background: rgba(245,158,11,.16); color: var(--ev-orange);}
        .ev-pill.red {background: rgba(220,38,38,.14); color: var(--ev-red);}
        .ev-kpi {padding: 16px; min-height: 106px;}
        .ev-kpi-label {font-size:.82rem; color: var(--ev-muted); margin-bottom:8px;}
        .ev-kpi-value {font-size:1.55rem; font-weight:800; line-height:1.1;}
        .ev-kpi-note {font-size:.84rem; color: var(--ev-muted); margin-top:8px;}
        .ev-card {padding: 17px; margin-bottom: 16px;}
        .ev-card h3 {font-size:1.02rem; margin:0 0 12px;}
        .ev-route-card {padding:14px; margin-bottom:10px; border-left: 5px solid var(--ev-blue);}
        .ev-route-card.efficient {border-left-color: var(--ev-green);}
        .ev-route-card.safe {border-left-color: var(--ev-orange);}
        .ev-route-card.selected {outline: 2px solid var(--ev-green);}
        .ev-route-name {font-weight:800; margin-bottom:6px;}
        .ev-route-meta {color: var(--ev-muted); font-size:.9rem;}
        .ev-carousel {
            background: linear-gradient(135deg, rgba(37,99,235,.10), rgba(25,169,116,.08));
            border: 1px solid var(--ev-border);
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0 16px;
            box-shadow: var(--ev-shadow);
        }
        .ev-carousel-top {display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px;}
        .ev-carousel-title {font-weight:800; font-size:1.08rem;}
        .ev-dots {display:flex; gap:6px;}
        .ev-dot {width:8px; height:8px; border-radius:999px; background:rgba(120,120,120,.35);}
        .ev-dot.active {background:var(--ev-green);}
        .ev-slide-grid {display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:10px;}
        .ev-slide-stat {background:rgba(255,255,255,.06); border:1px solid var(--ev-border); border-radius:8px; padding:11px;}
        .ev-table {width:100%; border-collapse: collapse; font-size:.92rem;}
        .ev-table th, .ev-table td {padding: 10px 8px; border-bottom: 1px solid var(--ev-border); text-align:left;}
        .ev-table th {color: var(--ev-muted); font-size:.78rem; text-transform:uppercase;}
        .ev-step {display:flex; gap:10px; padding:10px 0; border-bottom:1px solid var(--ev-border);}
        .ev-step-num {min-width:26px; height:26px; border-radius:50%; background:rgba(37,99,235,.12); color:var(--ev-blue); display:flex; align-items:center; justify-content:center; font-weight:800; font-size:.8rem;}
        .ev-risk-bar {height:8px; border-radius:999px; background:rgba(120,120,120,.16); overflow:hidden; margin-top:7px;}
        .ev-risk-fill {height:100%; border-radius:999px;}
        .ev-insights {padding:17px;}
        .ev-insights ul {margin: 8px 0 0 1.1rem; padding: 0;}
        .ev-insights li {margin: 7px 0;}
        .ev-map-frame {border:1px solid var(--ev-border); border-radius:8px; overflow:hidden; box-shadow: var(--ev-shadow);}
        .ev-section-label {font-weight:800; font-size:1.08rem; margin: 8px 0 10px;}
        @media (max-width: 760px) {
            .block-container {padding-left: .85rem; padding-right: .85rem;}
            .ev-hero {padding:16px;}
            .ev-title-row {display:block;}
            .ev-hero h1 {font-size:1.35rem;}
            .ev-hero-grid {grid-template-columns: repeat(2, minmax(0, 1fr)); gap:10px;}
            .ev-slide-grid {grid-template-columns: repeat(2, minmax(0, 1fr));}
            .ev-kpi {padding:13px; min-height:92px;}
            .ev-kpi-value {font-size:1.28rem;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def location_search(label: str, default_query: str, key: str) -> tuple[Location | None, list[str]]:
    if f"{key}_query" not in st.session_state:
        st.session_state[f"{key}_query"] = default_query
    query = st.text_input(label, key=f"{key}_query")
    if len(query.strip()) < 2:
        return st.session_state.get(f"{key}_location"), []

    results = cached_geocode(query, 8)
    if not results:
        st.error(f"No location matches found for '{query}'. Try a more specific place name.")
        return None, []

    labels = [result[2] for result in results]
    selected_label = st.selectbox(
        f"{label} matches",
        labels,
        key=f"{key}_match",
        label_visibility="collapsed",
    )
    latitude, longitude, display_name = next(result for result in results if result[2] == selected_label)
    location = Location(latitude, longitude, display_name)
    st.session_state[f"{key}_location"] = location
    return location, labels


def charging_status(summary: DecisionSummary) -> tuple[str, str, str, int]:
    if not summary.charging.required:
        return "No Charging Required", "green", "No", 0
    arrival = summary.estimated_battery_remaining_pct
    if arrival <= 8:
        return "Charging Required", "red", "Yes", 35
    return "Recommended Charging Stop", "orange", "Recommended", 20


def traffic_level(summary: DecisionSummary) -> str:
    eta_ratio = summary.route.travel_time_min / max(summary.route.distance_km, 1)
    if eta_ratio > 2.2:
        return "Heavy"
    if eta_ratio > 1.45:
        return "Moderate"
    return "Light"


def route_traffic_level(route) -> str:
    eta_ratio = route.travel_time_min / max(route.distance_km, 1)
    if eta_ratio > 2.2:
        return "Heavy"
    if eta_ratio > 1.45:
        return "Moderate"
    return "Light"


def efficiency_score(summary: DecisionSummary) -> int:
    base = 100
    base -= min(22, int(max(0, summary.energy.consumption_kwh_per_100km - 13) * 2.0))
    base -= {"Low": 0, "Moderate": 5, "High": 12}[summary.weather_risk]
    if summary.charging.required:
        base -= 7
    return max(45, min(99, base))


def current_route_score(summary: DecisionSummary) -> int:
    score = efficiency_score(summary)
    if traffic_level(summary) == "Heavy":
        score -= 12
    elif traffic_level(summary) == "Moderate":
        score -= 5
    if summary.estimated_battery_remaining_pct < 15:
        score -= 10
    return max(35, min(99, score))


def solar_gain_kwh(summary: DecisionSummary, factor: float = 1.0) -> float:
    daylight_hours = max(0.2, summary.route.travel_time_min / 60)
    return max(0.0, summary.solar.solar_power_kw * daylight_hours * factor)


def sunlight_factor_for_departure(departure: datetime) -> float:
    hour = departure.hour + departure.minute / 60
    if hour < 6 or hour > 18:
        return 0.08
    return max(0.18, min(1.0, 1 - abs(hour - 12) / 6))


def default_solar_departure() -> datetime:
    now = datetime.now().replace(second=0, microsecond=0)
    target = now.replace(hour=11, minute=30)
    if now.hour >= 15:
        target = target + timedelta(days=1)
    return target


def variant_profile(name: str) -> dict[str, float]:
    profiles = {
        "Fastest": {"time": 1.0, "energy": 1.0, "cloud": 1.08, "rain": 1.02, "exposure": 0.62, "traffic": 1.0},
        "Efficient": {"time": 1.07, "energy": 0.92, "cloud": 0.88, "rain": 0.9, "exposure": 0.76, "traffic": 0.85},
        "Weather Safe": {"time": 1.1, "energy": 1.02, "cloud": 0.72, "rain": 0.58, "exposure": 0.7, "traffic": 0.78},
        "Maximum Solar Gain": {"time": 1.16, "energy": 1.04, "cloud": 0.64, "rain": 0.72, "exposure": 0.9, "traffic": 0.88},
        "Fastest Route": {"time": 1.0, "energy": 1.0, "cloud": 1.08, "rain": 1.02, "exposure": 0.62, "traffic": 1.0},
        "Efficient Route": {"time": 1.07, "energy": 0.92, "cloud": 0.88, "rain": 0.9, "exposure": 0.76, "traffic": 0.85},
        "Weather Safe Route": {"time": 1.1, "energy": 1.02, "cloud": 0.72, "rain": 0.58, "exposure": 0.7, "traffic": 0.78},
        "Maximum Solar Gain Route": {"time": 1.16, "energy": 1.04, "cloud": 0.56, "rain": 0.62, "exposure": 0.94, "traffic": 0.84},
        "Solar Optimized Route": {"time": 1.12, "energy": 1.02, "cloud": 0.6, "rain": 0.65, "exposure": 0.92, "traffic": 0.84},
        "Alternative Route": {"time": 1.08, "energy": 1.0, "cloud": 0.82, "rain": 0.82, "exposure": 0.74, "traffic": 0.9},
        "OSRM Route": {"time": 1.0, "energy": 1.0, "cloud": 0.9, "rain": 0.9, "exposure": 0.7, "traffic": 1.0},
    }
    return profiles.get(name, profiles["Fastest"])


def solar_profile(summary: DecisionSummary, route_name: str = "Maximum Solar Gain", departure: datetime | None = None) -> list[dict[str, object]]:
    departure = departure or default_solar_departure()
    profile = variant_profile(route_name)
    segment_count = max(3, min(9, round(summary.route.distance_km / 5)))
    base_irradiance = max(850.0, summary.solar.irradiance_w_m2)
    daylight = sunlight_factor_for_departure(departure)
    rows: list[dict[str, object]] = []
    for index in range(segment_count):
        progress = index / max(segment_count - 1, 1)
        cloud = max(5.0, min(98.0, summary.weather.cloud_cover_pct * profile["cloud"] + (index % 3 - 1) * 8))
        rain = max(0.0, min(100.0, summary.weather.rain_probability_pct * profile["rain"] + progress * 10 - 4))
        exposure = max(0.25, min(0.96, profile["exposure"] - (0.08 if index % 4 == 1 else 0) + (0.05 if index % 4 == 3 else 0)))
        irradiance = max(0.0, base_irradiance * daylight * (1 - cloud / 145) * (1 - rain / 260) * exposure)
        route_hours = summary.route.travel_time_min * profile["time"] / 60
        duration_h = max(route_hours, SOLAR_PLANNING_WINDOW_H) / segment_count
        harvest = irradiance * SOLAR_ROOF_AREA_M2 * SOLAR_PANEL_EFFICIENCY * duration_h / 1000
        label = "Open highway" if exposure >= 0.82 else "Mixed road" if exposure >= 0.62 else "Urban shade"
        rows.append(
            {
                "segment": index + 1,
                "location": summary.route.waypoints[min(index, len(summary.route.waypoints) - 1)].name if summary.route.waypoints else f"Segment {index + 1}",
                "cloud": cloud,
                "rain": rain,
                "irradiance": irradiance,
                "exposure": exposure,
                "shade": label,
                "harvest": harvest,
            }
        )
    return rows


def total_solar_harvest(summary: DecisionSummary, route_name: str, departure: datetime | None = None) -> float:
    return sum(float(row["harvest"]) for row in solar_profile(summary, route_name, departure))


def average_cloud_rain(summary: DecisionSummary, route_name: str) -> tuple[float, float]:
    rows = solar_profile(summary, route_name)
    return (
        sum(float(row["cloud"]) for row in rows) / len(rows),
        sum(float(row["rain"]) for row in rows) / len(rows),
    )


def solar_route_score(summary: DecisionSummary, route_name: str) -> int:
    cloud, rain = average_cloud_rain(summary, route_name)
    exposure = variant_profile(route_name)["exposure"] * 100
    harvest = total_solar_harvest(summary, route_name)
    score = 42 + exposure * 0.3 + min(24, harvest * 9) - cloud * 0.18 - rain * 0.16
    return max(35, min(99, round(score)))


def battery_with_solar(summary: DecisionSummary, route_name: str) -> float:
    harvest = total_solar_harvest(summary, route_name)
    profile = variant_profile(route_name)
    energy_required = summary.route.energy_required_kwh * profile["energy"]
    battery_delta = (energy_required - harvest) / settings.usable_battery_kwh * 100
    current_soc_estimate = summary.estimated_battery_remaining_pct + summary.route.energy_required_kwh / settings.usable_battery_kwh * 100
    return max(0.0, min(100.0, current_soc_estimate - battery_delta))


def safe_range_km(summary: DecisionSummary) -> float:
    return max(0.0, summary.energy.remaining_range_km - max(20.0, summary.route.distance_km * 0.12))


def route_options(summary: DecisionSummary) -> list[dict[str, object]]:
    routes = summary.route_alternatives or [summary.route]
    options = []
    for route in routes:
        route_summary = summary_for_route(summary, route)
        name = route.route_name
        route_score = current_route_score(route_summary)
        solar_score = solar_route_score(route_summary, name)
        cloud, rain = average_cloud_rain(route_summary, name)
        score_weight = 0.74 if name == "Maximum Solar Gain Route" else 0.55
        score = round(route_score * (1 - score_weight) + solar_score * score_weight)
        options.append(
            {
                "name": name,
                "time": route.travel_time_min,
                "battery": battery_with_solar(route_summary, name),
                "solar": total_solar_harvest(route_summary, name),
                "traffic": route_traffic_level(route),
                "score": max(35, min(99, score)),
                "solar_score": solar_score,
                "cloud": cloud,
                "rain": rain,
                "route": route,
            }
        )
    return sorted(options, key=lambda option: int(option["score"]), reverse=True)


def summary_for_route(summary: DecisionSummary, route) -> DecisionSummary:
    current_soc_estimate = summary.estimated_battery_remaining_pct + summary.route.energy_required_kwh / settings.usable_battery_kwh * 100
    battery_remaining = max(0.0, current_soc_estimate - route.energy_required_kwh / settings.usable_battery_kwh * 100)
    energy = replace(summary.energy, energy_required_kwh=route.energy_required_kwh)
    return replace(summary, route=route, energy=energy, estimated_battery_remaining_pct=battery_remaining)


def selected_route_name(summary: DecisionSummary) -> str:
    names = [str(option["name"]) for option in route_options(summary)]
    selected = st.session_state.get("confirmed_route_option") or st.session_state.get("route_comparison_choice")
    if selected in names:
        return str(selected)
    return str(best_route_option(summary)["name"])


def selected_decision_summary(summary: DecisionSummary) -> DecisionSummary:
    name = selected_route_name(summary)
    option = next((option for option in route_options(summary) if option["name"] == name), best_route_option(summary))
    return summary_for_route(summary, option["route"])


def charging_station_views(summary: DecisionSummary) -> list[ChargingStationView]:
    brands = [
        ("Tata Power", "Available", 60, 21),
        ("Ather Grid", "Busy", 25, 18),
        ("ChargeZone", "Available", 90, 24),
        ("Statiq", "Available", 50, 20),
    ]
    if not summary.route.path:
        return []
    stations: list[ChargingStationView] = []
    for index, (name, availability, speed, cost) in enumerate(brands, start=1):
        point_index = min(len(summary.route.path) - 1, round(index * (len(summary.route.path) - 1) / (len(brands) + 1)))
        point = summary.route.path[point_index]
        stations.append(
            ChargingStationView(
                name=name,
                location=Location(point.latitude + 0.002 * index, point.longitude - 0.0015 * index, name),
                distance_km=summary.route.distance_km * index / (len(brands) + 1),
                availability=availability,
                speed_kw=speed,
                cost_per_kwh=cost,
            )
        )
    return stations


def risk_scores(summary: DecisionSummary) -> dict[str, int]:
    traffic = {"Light": 8, "Moderate": 25, "Heavy": 52}[traffic_level(summary)]
    weather = {"Low": 10, "Moderate": 32, "High": 62}[summary.weather_risk]
    battery = 5 if summary.estimated_battery_remaining_pct > 20 else 28 if summary.estimated_battery_remaining_pct > 10 else 65
    charging = 2 if not summary.charging.required else 24
    return {"Weather Risk": weather, "Traffic Risk": traffic, "Battery Risk": battery, "Charging Risk": charging}


def render_hero(summary: DecisionSummary, current_soc: float) -> None:
    status, tone, charging_label, _ = charging_status(summary)
    reachable = summary.estimated_battery_remaining_pct > 8
    headline = "Destination Reachable" if reachable else "Charging Needed Before Arrival"
    badge_tone = "green" if reachable else "red"
    st.markdown(
        f"""
        <div class="ev-hero">
            <div class="ev-title-row">
                <div>
                    <span class="ev-pill {badge_tone}">{headline}</span>
                    <h1>{summary.route.destination.label or "Your destination"}</h1>
                    <div class="ev-subtle">Smart EV route plan updated {datetime.now().strftime("%I:%M %p")}</div>
                </div>
                <span class="ev-pill {tone}">{status}</span>
            </div>
            <div class="ev-hero-grid">
                <div><div class="ev-kpi-label">Distance</div><div class="ev-kpi-value">{summary.route.distance_km:.1f} km</div></div>
                <div><div class="ev-kpi-label">ETA</div><div class="ev-kpi-value">{summary.route.travel_time_min:.0f} min</div></div>
                <div><div class="ev-kpi-label">Battery</div><div class="ev-kpi-value">{current_soc:.0f}% -> {summary.estimated_battery_remaining_pct:.0f}%</div></div>
                <div><div class="ev-kpi-label">Weather</div><div class="ev-kpi-value">{summary.weather.temperature_c:.0f} C</div><div class="ev-kpi-note">{summary.weather.rain_probability_pct:.0f}% rain chance</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_route_source_warning(summary: DecisionSummary) -> None:
    if summary.route.source.startswith("osrm"):
        return
    st.warning(
        "Road routing service is unavailable, so this trip is using an approximate fallback route. "
        "Connect to the internet and click Find Best Route again for road-following navigation."
    )


def best_route_option(summary: DecisionSummary) -> dict[str, object]:
    return max(route_options(summary), key=lambda option: int(option["score"]))


def fastest_route_option(summary: DecisionSummary) -> dict[str, object]:
    return min(route_options(summary), key=lambda option: float(option["time"]))


def option_css_name(name: object) -> str:
    return str(name).lower().replace(" ", "_")


def set_selected_route(name: object) -> None:
    st.session_state.confirmed_route_option = str(name)
    st.session_state.route_confirmed = True
    st.session_state.travel_started = False
    st.session_state.show_alternatives = False


def render_alternative_slider(summary: DecisionSummary) -> None:
    options = route_options(summary)
    best = best_route_option(summary)
    if "alternative_index" not in st.session_state:
        st.session_state.alternative_index = next(
            (index for index, option in enumerate(options) if option["name"] == best["name"]),
            0,
        )
    st.session_state.alternative_index = st.session_state.alternative_index % len(options)
    option = options[st.session_state.alternative_index]
    dots = "".join(
        f"<span class='ev-dot {'active' if index == st.session_state.alternative_index else ''}'></span>"
        for index in range(len(options))
    )
    st.markdown(
        f"""
        <div class="ev-carousel">
            <div class="ev-carousel-top">
                <div>
                    <div class="ev-carousel-title">{escape(str(option["name"]))} Route</div>
                    <div class="ev-subtle">Swipe-style route review</div>
                </div>
                <div class="ev-dots">{dots}</div>
            </div>
            <div class="ev-slide-grid">
                <div class="ev-slide-stat"><div class="ev-kpi-label">Time</div><div class="ev-kpi-value">{float(option["time"]):.0f} min</div></div>
                <div class="ev-slide-stat"><div class="ev-kpi-label">Battery</div><div class="ev-kpi-value">{float(option["battery"]):.0f}%</div></div>
                <div class="ev-slide-stat"><div class="ev-kpi-label">Solar</div><div class="ev-kpi-value">{float(option["solar"]):.1f} kWh</div></div>
                <div class="ev-slide-stat"><div class="ev-kpi-label">Score</div><div class="ev-kpi-value">{int(option["score"])}/100</div></div>
            </div>
            <div class="ev-subtle" style="margin-top:12px;">Traffic: {escape(str(option["traffic"]))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    prev_col, select_col, next_col = st.columns([1, 1.35, 1])
    with prev_col:
        if st.button("Previous", use_container_width=True, key="alt_prev"):
            st.session_state.alternative_index = (st.session_state.alternative_index - 1) % len(options)
            st.rerun()
    with select_col:
        if st.button("Select this route", type="primary", use_container_width=True, key="alt_select"):
            set_selected_route(option["name"])
            st.rerun()
    with next_col:
        if st.button("Next", use_container_width=True, key="alt_next"):
            st.session_state.alternative_index = (st.session_state.alternative_index + 1) % len(options)
            st.rerun()


def render_ai_route_decision(summary: DecisionSummary) -> None:
    best = best_route_option(summary)
    if st.session_state.get("route_confirmed", False):
        selected = st.session_state.get("confirmed_route_option", str(best["name"]))
        selected_option = next((option for option in route_options(summary) if option["name"] == selected), best)
        fastest = fastest_route_option(summary)
        cloud_delta = float(fastest["cloud"]) - float(selected_option["cloud"])
        rain_delta = float(fastest["rain"]) - float(selected_option["rain"])
        solar_delta = float(selected_option["solar"]) - float(fastest["solar"])
        extra_range = float(selected_option["solar"]) / KWH_PER_KM
        battery_delta = float(selected_option["battery"]) - float(fastest["battery"])
        reasons = [
            f"{max(0.0, cloud_delta):.0f}% lower cloud cover",
            f"{max(0.0, rain_delta):.0f}% lower rain exposure",
            f"+{max(0.0, solar_delta):.1f} kWh solar recovery",
            f"+{extra_range:.0f} km additional solar range",
            f"Arrival battery improves from {float(fastest['battery']):.0f}% to {float(selected_option['battery']):.0f}%",
        ]
        if battery_delta <= 0:
            reasons[-1] = f"Arrival battery {float(selected_option['battery']):.0f}% with solar recovery"
        st.markdown(
            f"""
            <div class="ev-card">
                <span class="ev-pill green">AI Recommendation</span>
                <div style="margin-top:12px; font-size:1.04rem; font-weight:700;">Selected Route: {escape(str(selected_option["name"]))}</div>
                <ul style="margin:10px 0 0 1.1rem; padding:0;">
                    {''.join(f'<li>{escape(reason)}</li>' for reason in reasons)}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        action_col, review_col = st.columns(2)
        with action_col:
            if st.button("Start Travelling", type="primary", use_container_width=True, key="start_from_advisor"):
                st.session_state.travel_started = True
                st.rerun()
        with review_col:
            if st.button("Change Route", use_container_width=True, key="change_from_advisor"):
                st.session_state.route_confirmed = False
                st.session_state.travel_started = False
                st.session_state.show_alternatives = True
                st.rerun()
        if st.session_state.get("show_alternatives", False):
            render_alternative_slider(summary)
        return

    continue_ready = summary.estimated_battery_remaining_pct > 8
    recommendation = (
        f"AI recommends the {best['name']} route because it gives the strongest sunlight-weather balance. "
        f"Solar score is {int(best['solar_score'])}/100, expected harvest is {float(best['solar']):.1f} kWh, "
        f"average cloud cover is {float(best['cloud']):.0f}%, and arrival battery is {float(best['battery']):.0f}%."
    )
    if summary.charging.required:
        recommendation += " Add the suggested charging stop before continuing."
    elif summary.weather_risk != "Low":
        recommendation += " Continue with weather caution."
    else:
        recommendation += " Conditions look good to continue."
    tone = "green" if continue_ready else "red"
    st.markdown(
        f"""
        <div class="ev-card">
            <span class="ev-pill {tone}">AI Route Advisor</span>
            <div style="margin-top:12px; font-size:1.04rem; font-weight:700;">{escape(recommendation)}</div>
            <div class="ev-subtle" style="margin-top:8px;">Do you want to continue with this route?</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    yes_col, no_col = st.columns(2)
    with yes_col:
        if st.button("Yes, continue", type="primary", use_container_width=True):
            set_selected_route(best["name"])
            st.rerun()
    with no_col:
        if st.button("Review alternatives", use_container_width=True):
            st.session_state.route_confirmed = False
            st.session_state.travel_started = False
            st.session_state.show_alternatives = True
            st.session_state.alternative_index = next(
                (index for index, option in enumerate(route_options(summary)) if option["name"] == best["name"]),
                0,
            )
            st.rerun()
    if st.session_state.get("show_alternatives", False):
        render_alternative_slider(summary)


def render_travel_controls(summary: DecisionSummary) -> None:
    confirmed = st.session_state.get("route_confirmed", False)
    started = st.session_state.get("travel_started", False)
    if not confirmed:
        st.info("Choose a route above before starting travel.")
        return
    if not started:
        selected = st.session_state.get("confirmed_route_option", str(best_route_option(summary)["name"]))
        st.success(f"{selected} route selected. Press Start Travelling above when ready.")
        return
    next_step = summary.route.steps[0].instruction if summary.route.steps else "Continue on selected route"
    st.success(f"Trip started. Next: {next_step}")
    progress = min(0.18, max(0.04, 8 / max(summary.route.travel_time_min, 1)))
    st.progress(progress, text="Live navigation active")


def render_kpi_cards(summary: DecisionSummary) -> None:
    status, tone, charging_label, charging_minutes = charging_status(summary)
    items = [
        ("Battery on Arrival", f"{summary.estimated_battery_remaining_pct:.0f}%", f"Current range {summary.energy.remaining_range_km:.0f} km"),
        ("ETA", f"{summary.route.travel_time_min:.0f} min", traffic_level(summary) + " traffic"),
        ("Distance", f"{summary.route.distance_km:.1f} km", f"{summary.route.energy_required_kwh:.1f} kWh required"),
        ("Charging Status", charging_label, f"{charging_minutes} min estimated stop" if charging_minutes else "No stop needed"),
    ]
    cols = st.columns(4)
    for col, (label, value, note) in zip(cols, items):
        col.markdown(
            f"""
            <div class="ev-kpi">
                <div class="ev-kpi-label">{label}</div>
                <div class="ev-kpi-value">{value}</div>
                <div class="ev-kpi-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_compact_solar_outcome(summary: DecisionSummary) -> None:
    option = next((option for option in route_options(summary) if option["name"] == selected_route_name(summary)), best_route_option(summary))
    rain_label = "Low" if float(option["rain"]) < 25 else "Moderate" if float(option["rain"]) < 55 else "High"
    st.markdown(
        f"""
        <div class="ev-card">
            <h3>Solar Trip Outcome</h3>
            <div class="ev-hero-grid">
                <div><div class="ev-kpi-label">Solar Gain</div><div class="ev-kpi-value">+{float(option["solar"]):.1f} kWh</div></div>
                <div><div class="ev-kpi-label">Arrival Battery</div><div class="ev-kpi-value">{float(option["battery"]):.0f}%</div></div>
                <div><div class="ev-kpi-label">Rain Risk</div><div class="ev-kpi-value">{rain_label}</div></div>
                <div><div class="ev-kpi-label">Solar Score</div><div class="ev-kpi-value">{int(option["solar_score"])}/100</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_weather_row(summary: DecisionSummary) -> None:
    score = efficiency_score(summary)
    cols = st.columns(3)
    cards = [
        ("Weather Impact", summary.weather_risk.upper(), f"{summary.weather.temperature_c:.0f} C, {summary.weather.rain_probability_pct:.0f}% rain"),
        ("Efficiency Score", f"{score}/100", "Higher is better"),
        ("Range Health", f"{safe_range_km(summary):.0f} km safe", f"{summary.energy.remaining_range_km:.0f} km current range"),
    ]
    for col, (label, value, note) in zip(cols, cards):
        col.markdown(
            f"""
            <div class="ev-kpi">
                <div class="ev-kpi-label">{label}</div>
                <div class="ev-kpi-value">{value}</div>
                <div class="ev-kpi-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def route_dataframe(path: list[Location]) -> pd.DataFrame:
    return pd.DataFrame({"lat": [p.latitude for p in path], "lon": [p.longitude for p in path]})


def route_color(name: str) -> str:
    colors = {
        "Fastest Route": "#2563eb",
        "Efficient Route": "#7c3aed",
        "Weather Safe Route": "#facc15",
        "Maximum Solar Gain Route": "#19a974",
    }
    return colors.get(name, "#2563eb")


def route_popup_html(option: dict[str, object]) -> str:
    route = option["route"]
    return (
        f"<b>{escape(str(option['name']))}</b><br>"
        f"Distance: {route.distance_km:.1f} km<br>"
        f"ETA: {float(option['time']):.0f} min<br>"
        f"Solar Gain: {float(option['solar']):.1f} kWh<br>"
        f"Rain Risk: {float(option['rain']):.0f}%<br>"
        f"Cloud Cover: {float(option['cloud']):.0f}%<br>"
        f"Arrival Battery: {float(option['battery']):.0f}%"
    )


def build_folium_map(summary: DecisionSummary, base_summary: DecisionSummary | None = None):
    import folium

    base_summary = base_summary or summary
    options = route_options(base_summary)
    selected_name = selected_route_name(base_summary)
    all_points = [point for option in options for point in option["route"].path]
    points = [(point.latitude, point.longitude) for point in (all_points or summary.route.path)]
    center = points[len(points) // 2] if points else (summary.route.start.latitude, summary.route.start.longitude)
    fmap = folium.Map(location=center, zoom_start=12, tiles="CartoDB positron", control_scale=True)
    for option in sorted(options, key=lambda item: 1 if item["name"] == selected_name else 0):
        route = option["route"]
        route_points = [(point.latitude, point.longitude) for point in route.path]
        is_selected = option["name"] == selected_name
        folium.PolyLine(
            route_points,
            color=route_color(str(option["name"])),
            weight=10 if is_selected else 4,
            opacity=0.98 if is_selected else 0.5,
            tooltip=f"{option['name']} {'(selected)' if is_selected else ''}",
            popup=folium.Popup(route_popup_html(option), max_width=290),
        ).add_to(fmap)
        if is_selected and route_points:
            label_point = route_points[len(route_points) // 2]
            folium.Marker(
                label_point,
                tooltip=str(option["name"]),
                icon=folium.DivIcon(
                    html=f"<div style='background:{route_color(str(option['name']))}; color:white; padding:4px 8px; border-radius:999px; font-weight:700; white-space:nowrap;'>{escape(str(option['name']))}</div>"
                ),
            ).add_to(fmap)
    traffic_colors = {"fast": "#19a974", "moderate": "#facc15", "slow": "#dc2626", "congested": "#dc2626"}
    for segment in summary.route.traffic_segments:
        segment_points = [(point.latitude, point.longitude) for point in segment.path] or [
            (segment.start.latitude, segment.start.longitude),
            (segment.end.latitude, segment.end.longitude),
        ]
        folium.PolyLine(
            segment_points,
            color=traffic_colors.get(segment.status, "#19a974"),
            weight=3,
            opacity=0.92,
            tooltip=f"{segment.status.title()} traffic",
        ).add_to(fmap)
    folium.Marker(
        [summary.route.start.latitude, summary.route.start.longitude],
        tooltip="Start",
        popup=summary.route.start.label or "Start",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(fmap)
    folium.Marker(
        [summary.route.destination.latitude, summary.route.destination.longitude],
        tooltip="Destination",
        popup=summary.route.destination.label or "Destination",
        icon=folium.Icon(color="blue", icon="flag-checkered", prefix="fa"),
    ).add_to(fmap)
    for stop in summary.charging.stops:
        folium.Marker(
            [stop.location.latitude, stop.location.longitude],
            tooltip="Charging stop",
            popup=f"{stop.name}<br>{stop.distance_from_start_km:.1f} km from start",
            icon=folium.Icon(color="orange", icon="bolt", prefix="fa"),
        ).add_to(fmap)
    for station in charging_station_views(summary):
        folium.Marker(
            [station.location.latitude, station.location.longitude],
            tooltip=station.name,
            popup=f"{station.name}<br>{station.availability}<br>{station.speed_kw} kW<br>Rs {station.cost_per_kwh}/kWh",
            icon=folium.Icon(color="purple", icon="bolt", prefix="fa"),
        ).add_to(fmap)
    for waypoint in summary.route.waypoints[1:-1]:
        color = "red" if "rain" in waypoint.weather.lower() else "lightgray" if "cloud" in waypoint.weather.lower() else "orange"
        icon = "umbrella" if "rain" in waypoint.weather.lower() else "cloud" if "cloud" in waypoint.weather.lower() else "sun"
        folium.Marker(
            [waypoint.location.latitude, waypoint.location.longitude],
            tooltip=waypoint.name,
            popup=f"{waypoint.name}<br>{waypoint.weather}<br>{waypoint.solar_score}",
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
        ).add_to(fmap)
    for waypoint in summary.route.waypoints:
        solar_color = "#facc15" if waypoint.solar_score == "High solar" else "#94a3b8"
        folium.CircleMarker(
            [waypoint.location.latitude, waypoint.location.longitude],
            radius=10,
            color=solar_color,
            fill=True,
            fill_opacity=0.22,
            tooltip=waypoint.solar_score,
        ).add_to(fmap)
    if summary.weather_risk != "Low":
        folium.CircleMarker(
            center,
            radius=18,
            color="#f59e0b" if summary.weather_risk == "Moderate" else "#dc2626",
            fill=True,
            fill_opacity=0.18,
            tooltip=f"{summary.weather_risk} weather risk",
        ).add_to(fmap)
    folium.CircleMarker(
        center,
        radius=8,
        color="#19a974" if traffic_level(summary) == "Light" else "#f59e0b",
        fill=True,
        fill_opacity=0.8,
        tooltip=f"{traffic_level(summary)} traffic",
    ).add_to(fmap)
    legend = """
    <div style="position: fixed; bottom: 28px; left: 28px; z-index: 9999; background: white; color: #111827; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 13px;">
      <b>Routes</b><br>
      <span style="color:#2563eb;">━━</span> Fastest<br>
      <span style="color:#7c3aed;">━━</span> Efficient<br>
      <span style="color:#facc15;">━━</span> Weather Safe<br>
      <span style="color:#19a974;">━━</span> Maximum Solar Gain<br>
      <span style="color:#dc2626;">━━</span> Heavy Traffic
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend))
    if points:
        lats = [point[0] for point in points]
        lons = [point[1] for point in points]
        fmap.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(28, 28))
    return fmap


def render_map(summary: DecisionSummary, base_summary: DecisionSummary | None = None) -> None:
    st.markdown('<div class="ev-section-label">Route Map</div>', unsafe_allow_html=True)
    try:
        from streamlit_folium import st_folium

        st.markdown('<div class="ev-map-frame">', unsafe_allow_html=True)
        st_folium(build_folium_map(summary, base_summary), height=460, use_container_width=True, returned_objects=[])
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception:
        st.map(route_dataframe(summary.route.path), latitude="lat", longitude="lon", zoom=11)


def render_route_details(summary: DecisionSummary) -> None:
    road_chain = " -> ".join(summary.route.road_names[:4]) if summary.route.road_names else "Road network route"
    st.markdown(
        f"""
        <div class="ev-card">
            <h3>Recommended Route</h3>
            <div class="ev-hero-grid">
                <div><div class="ev-kpi-label">Distance</div><div class="ev-kpi-value">{summary.route.distance_km:.1f} km</div></div>
                <div><div class="ev-kpi-label">ETA</div><div class="ev-kpi-value">{summary.route.travel_time_min:.0f} min</div></div>
                <div><div class="ev-kpi-label">Energy Required</div><div class="ev-kpi-value">{summary.route.energy_required_kwh:.1f} kWh</div></div>
                <div><div class="ev-kpi-label">Battery Upon Arrival</div><div class="ev-kpi-value">{summary.estimated_battery_remaining_pct:.0f}%</div></div>
            </div>
            <div class="ev-subtle" style="margin-top:12px;">Weather risk: {summary.weather_risk} | Traffic level: {traffic_level(summary)}</div>
            <div class="ev-subtle" style="margin-top:7px;">Roads: {escape(road_chain)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_charging(summary: DecisionSummary) -> None:
    status, tone, _, minutes = charging_status(summary)
    detail = "You can complete this trip without stopping." if not summary.charging.required else summary.charging.message
    if summary.charging.stops:
        stop = summary.charging.stops[0]
        detail += f" Suggested stop: {stop.name}, about {stop.distance_from_start_km:.1f} km from start."
    st.markdown(
        f"""
        <div class="ev-card">
            <span class="ev-pill {tone}">{status}</span>
            <div style="margin-top:12px; font-size:1.05rem; font-weight:700;">Estimated charging time: {minutes} min</div>
            <div class="ev-subtle" style="margin-top:7px;">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_route_comparison(summary: DecisionSummary) -> None:
    st.markdown('<div class="ev-section-label">Solar-Aware Route Comparison</div>', unsafe_allow_html=True)
    options = route_options(summary)
    option_names = [str(option["name"]) for option in options]
    if st.session_state.get("route_comparison_choice") not in option_names:
        st.session_state.route_comparison_choice = str(best_route_option(summary)["name"])
    selected = st.radio(
        "Select Route",
        option_names,
        horizontal=True,
        label_visibility="collapsed",
        key="route_comparison_choice",
    )
    rows = []
    for option in options:
        rows.append(
            {
                "Route": option["name"],
                "Time": f"{float(option['time']):.0f} min",
                "Battery": f"{float(option['battery']):.0f}%",
                "Solar": f"{float(option['solar']):.1f} kWh",
                "Solar Score": f"{int(option['solar_score'])}/100",
                "Cloud": f"{float(option['cloud']):.0f}%",
                "Rain": f"{float(option['rain']):.0f}%",
                "Traffic": option["traffic"],
                "Score": f"{int(option['score'])}/100",
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    chosen = next(option for option in options if option["name"] == selected)
    st.markdown(
        f"""
        <div class="ev-route-card selected">
            <div class="ev-route-name">{chosen["name"]} route selected</div>
            <div class="ev-route-meta">Score {int(chosen["score"])}/100 | Solar score {int(chosen["solar_score"])}/100 | Arrival battery {float(chosen["battery"]):.0f}% | Solar gain {float(chosen["solar"]):.1f} kWh</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Use this route", type="primary", use_container_width=True, key="comparison_use_route"):
        set_selected_route(chosen["name"])
        st.rerun()


def render_insights(summary: DecisionSummary) -> None:
    departure = datetime.now() + timedelta(minutes=12 if summary.weather_risk == "Low" else 35)
    heavy_segment = next((segment for segment in summary.route.traffic_segments if segment.status in {"slow", "congested"}), None)
    best = best_route_option(summary)
    fastest = fastest_route_option(summary)
    solar_delta = float(best["solar"]) - float(fastest["solar"])
    cloud_delta = float(fastest["cloud"]) - float(best["cloud"])
    rain_delta = float(fastest["rain"]) - float(best["rain"])
    traffic_note = (
        f"{heavy_segment.status.title()} traffic detected on one route segment; alternative routing may save 5-8 minutes."
        if heavy_segment
        else "Traffic is currently favorable along the selected route."
    )
    insights = [
        f"{best['name']} selected because it recovers {float(best['solar']):.1f} kWh from the solar roof.",
        f"Compared with Fastest, it adds {solar_delta:.1f} kWh solar gain and reduces average cloud cover by {cloud_delta:.0f}%.",
        f"Rain exposure changes by {-rain_delta:.0f}% versus the fastest route.",
        traffic_note,
        f"Recommended departure: {departure.strftime('%I:%M %p')}.",
        f"Estimated battery on arrival with solar recovery: {float(best['battery']):.0f}%.",
    ]
    st.markdown(
        "<div class='ev-insights'><h3>AI Trip Insights</h3><ul>"
        + "".join(f"<li>{item}</li>" for item in insights)
        + "</ul></div>",
        unsafe_allow_html=True,
    )


def render_weather_along_route(summary: DecisionSummary) -> None:
    rows = []
    for waypoint in summary.route.waypoints:
        rows.append(
            {
                "Location": waypoint.name,
                "ETA": f"+{waypoint.eta_min:.0f} min",
                "Weather": waypoint.weather,
                "Solar": waypoint.solar_score,
            }
        )
    st.markdown('<div class="ev-section-label">Weather Along Route</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_route_conditions(summary: DecisionSummary) -> None:
    selected_name = selected_route_name(summary)
    solar_rows = solar_profile(summary, selected_name)
    rows = []
    for index, row in enumerate(solar_rows):
        waypoint = summary.route.waypoints[min(index, len(summary.route.waypoints) - 1)] if summary.route.waypoints else None
        rows.append(
            {
                "Location": waypoint.name if waypoint else row["location"],
                "Weather": waypoint.weather if waypoint else ("Sunny" if float(row["cloud"]) < 40 else "Cloudy"),
                "Cloud": f"{float(row['cloud']):.0f}%",
                "Rain": f"{float(row['rain']):.0f}%",
                "Solar": f"{float(row['irradiance']):.0f} W/m2",
                "Sun Exposure": f"{float(row['exposure']) * 100:.0f}%",
                "Harvest": f"{float(row['harvest']):.2f} kWh",
            }
        )
    st.markdown('<div class="ev-section-label">Weather and Solar Along Route</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_solar_route_profile(summary: DecisionSummary) -> None:
    selected_name = st.session_state.get("confirmed_route_option") or str(best_route_option(summary)["name"])
    rows = []
    for row in solar_profile(summary, selected_name):
        rows.append(
            {
                "Segment": f"{int(row['segment'])}",
                "Location": row["location"],
                "Cloud": f"{float(row['cloud']):.0f}%",
                "Rain": f"{float(row['rain']):.0f}%",
                "Solar Radiation": f"{float(row['irradiance']):.0f} W/m2",
                "Sun Exposure": f"{float(row['exposure']) * 100:.0f}%",
                "Shade": row["shade"],
                "Harvest": f"{float(row['harvest']):.2f} kWh",
            }
        )
    st.markdown('<div class="ev-section-label">Solar and Cloud Cover Along Route</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def departure_options(summary: DecisionSummary) -> list[dict[str, object]]:
    now = datetime.now().replace(second=0, microsecond=0)
    route_name = str(best_route_option(summary)["name"])
    offsets = [0, 60, 120, 180]
    rows = []
    for offset in offsets:
        departure = now + timedelta(minutes=offset)
        harvest = total_solar_harvest(summary, route_name, departure)
        rows.append(
            {
                "departure": departure,
                "solar": harvest,
                "battery": min(100.0, battery_with_solar(summary, route_name) + harvest / settings.usable_battery_kwh * 100),
                "score": round(solar_route_score(summary, route_name) * sunlight_factor_for_departure(departure)),
            }
        )
    return rows


def render_departure_optimizer(summary: DecisionSummary) -> None:
    options = departure_options(summary)
    best = max(options, key=lambda row: float(row["solar"]))
    rows = [
        {
            "Leave At": row["departure"].strftime("%I:%M %p"),
            "Solar Gain": f"{float(row['solar']):.1f} kWh",
            "Arrival Battery": f"{float(row['battery']):.0f}%",
            "Sunlight Score": f"{int(row['score'])}/100",
        }
        for row in options
    ]
    st.markdown('<div class="ev-section-label">Departure Time Optimization</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="ev-card">
            <span class="ev-pill green">Best Departure</span>
            <div style="margin-top:10px; font-weight:800;">Leave at {best["departure"].strftime("%I:%M %p")} for maximum solar generation.</div>
            <div class="ev-subtle" style="margin-top:7px;">Expected solar gain: {float(best["solar"]):.1f} kWh</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_solar_roof_impact(summary: DecisionSummary) -> None:
    route_name = st.session_state.get("confirmed_route_option") or str(best_route_option(summary)["name"])
    harvest = total_solar_harvest(summary, route_name)
    extra_range = harvest / KWH_PER_KM
    battery_saved = harvest / settings.usable_battery_kwh * 100
    cols = st.columns(3)
    cards = [
        ("Solar Energy Recovered", f"{harvest:.1f} kWh", f"{SOLAR_ROOF_AREA_M2:.1f} m2 roof, {SOLAR_PANEL_EFFICIENCY * 100:.0f}% efficiency"),
        ("Battery Saved", f"{battery_saved:.1f}%", "Recovered in route sunlight window"),
        ("Extra Range Added", f"{extra_range:.1f} km", "Solar-assisted range"),
    ]
    for col, (label, value, note) in zip(cols, cards):
        col.markdown(
            f"""
            <div class="ev-kpi">
                <div class="ev-kpi-label">{label}</div>
                <div class="ev-kpi-value">{value}</div>
                <div class="ev-kpi-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_ai_route_explanation(summary: DecisionSummary) -> None:
    best = best_route_option(summary)
    fastest = fastest_route_option(summary)
    reasons = [
        f"{float(best['cloud']):.0f}% average cloud cover on the selected route.",
        f"{float(best['solar']) - float(fastest['solar']):.1f} kWh more solar gain than the fastest route.",
        f"{float(fastest['rain']) - float(best['rain']):.0f}% lower rain exposure than the fastest route.",
        f"Arrival battery improves to about {float(best['battery']):.0f}% after solar recovery.",
        f"Sun exposure profile favors {variant_profile(str(best['name']))['exposure'] * 100:.0f}% open-sky driving.",
    ]
    st.markdown(
        "<div class='ev-insights'><h3>Why AI Selected This Route</h3><ul>"
        + "".join(f"<li>{escape(reason)}</li>" for reason in reasons)
        + "</ul></div>",
        unsafe_allow_html=True,
    )


def render_charging_layer(summary: DecisionSummary) -> None:
    rows = []
    for station in charging_station_views(summary):
        rows.append(
            {
                "Station": station.name,
                "Distance": f"{station.distance_km:.1f} km",
                "Availability": station.availability,
                "Speed": f"{station.speed_kw} kW",
                "Cost": f"Rs {station.cost_per_kwh}/kWh",
            }
        )
    st.markdown('<div class="ev-section-label">EV Charging Layer</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_turn_by_turn(summary: DecisionSummary) -> None:
    st.markdown('<div class="ev-section-label">Turn-by-Turn Navigation</div>', unsafe_allow_html=True)
    steps = summary.route.steps[:10]
    if not steps:
        st.caption("Turn instructions are available when OSRM or OSM routing is reachable.")
        return
    html = "<div class='ev-card'>"
    for index, step in enumerate(steps, start=1):
        html += (
            f"<div class='ev-step'><div class='ev-step-num'>{index}</div>"
            f"<div><strong>{escape(step.instruction)}</strong>"
            f"<div class='ev-subtle'>{step.distance_km:.1f} km | {step.duration_min:.0f} min</div></div></div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_timeline(summary: DecisionSummary) -> None:
    start_time = datetime.now().replace(second=0, microsecond=0)
    rows = []
    for waypoint in summary.route.waypoints:
        rows.append(
            {
                "Time": (start_time + timedelta(minutes=waypoint.eta_min)).strftime("%I:%M %p"),
                "Stop": waypoint.name,
                "Condition": waypoint.weather,
            }
        )
    st.markdown('<div class="ev-section-label">Route Timeline</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_risk_score(summary: DecisionSummary) -> None:
    scores = risk_scores(summary)
    overall = int(sum(scores.values()) / len(scores))
    label = "LOW" if overall < 25 else "MODERATE" if overall < 50 else "HIGH"
    color = "#19a974" if label == "LOW" else "#f59e0b" if label == "MODERATE" else "#dc2626"
    html = f"<div class='ev-card'><h3>Route Risk Score</h3><div class='ev-kpi-value' style='color:{color};'>{label}</div>"
    for name, value in scores.items():
        bar_color = "#19a974" if value < 25 else "#f59e0b" if value < 50 else "#dc2626"
        html += (
            f"<div style='margin-top:12px;'><div class='ev-subtle'>{name}: {value}%</div>"
            f"<div class='ev-risk-bar'><div class='ev-risk-fill' style='width:{value}%; background:{bar_color};'></div></div></div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_live_rerouting(summary: DecisionSummary) -> None:
    current_score = current_route_score(summary)
    new_score = min(99, current_score + (19 if traffic_level(summary) != "Light" or summary.weather_risk != "Low" else 3))
    reason = "Heavy rain or congestion detected ahead." if new_score - current_score > 10 else "Current route is stable. No major reroute needed."
    st.markdown(
        f"""
        <div class="ev-card">
            <h3>Live Re-routing Advisor</h3>
            <div class="ev-subtle">{reason}</div>
            <div class="ev-hero-grid" style="margin-top:12px;">
                <div><div class="ev-kpi-label">Current Route Score</div><div class="ev-kpi-value">{current_score}/100</div></div>
                <div><div class="ev-kpi-label">Alternative Score</div><div class="ev-kpi-value">{new_score}/100</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if new_score - current_score > 8:
        st.button("Switch Route", type="primary", use_container_width=True)


def render_advanced(summary: DecisionSummary, road_gradient_pct: float) -> None:
    with st.expander("Advanced Analytics"):
        cols = st.columns(3)
        cols[0].metric("Solar irradiance", f"{summary.solar.irradiance_w_m2:.0f} W/m2")
        cols[1].metric("Humidity", f"{summary.weather.humidity_pct:.0f}%")
        cols[2].metric("Wind speed", f"{summary.weather.wind_speed_mps:.1f} m/s")
        cols = st.columns(3)
        cols[0].metric("Road gradient", f"{road_gradient_pct:.1f}%")
        cols[1].metric("Energy model", summary.energy.source)
        cols[2].metric("Route source", summary.route.source)
        st.dataframe(
            pd.DataFrame(
                [
                    {"Metric": "Cloud cover", "Value": f"{summary.weather.cloud_cover_pct:.0f}%"},
                    {"Metric": "Solar power estimate", "Value": f"{summary.solar.solar_power_kw:.2f} kW"},
                    {"Metric": "Consumption", "Value": f"{summary.energy.consumption_kwh_per_100km:.1f} kWh/100 km"},
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )


def render_efficiency_chart(summary: DecisionSummary) -> None:
    try:
        import plotly.graph_objects as go

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=efficiency_score(summary),
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Route Efficiency"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#19a974"},
                    "steps": [
                        {"range": [0, 60], "color": "rgba(220,38,38,.18)"},
                        {"range": [60, 82], "color": "rgba(245,158,11,.18)"},
                        {"range": [82, 100], "color": "rgba(25,169,116,.18)"},
                    ],
                },
            )
        )
        fig.update_layout(height=240, margin={"l": 18, "r": 18, "t": 45, "b": 10})
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.metric("Route Efficiency", f"{efficiency_score(summary)}/100")


def main() -> None:
    st.set_page_config(page_title="EV Smart Route Planner", page_icon="EV", layout="wide")
    inject_styles()

    st.markdown("### EV Smart Route Planner")
    st.caption("Plan a trip, check arrival battery, and decide whether you need to charge.")

    with st.sidebar:
        st.header("Plan Trip")
        start_location, start_matches = location_search("Start Location", "", "start")
        if st.button("Use Current Location", use_container_width=True):
            st.session_state.start_location = configured_current_location()
            start_location = st.session_state.start_location
        destination, dest_matches = location_search("Destination", "", "destination")
        soc = st.slider("Battery", 0.0, 100.0, settings.default_soc, help="Current battery state of charge.")
        speed = st.slider("Driving style", 30.0, 110.0, 55.0, help="Lower is gentler and usually more efficient.")
        with st.expander("Advanced trip settings"):
            gradient = st.slider("Road gradient", -10.0, 12.0, 1.0)
        run = st.button("Find Best Route", type="primary", use_container_width=True)

    with st.sidebar.expander("Search matches"):
        st.write("Start")
        st.caption(start_matches[0] if start_matches else "No selected match yet")
        st.write("Destination")
        st.caption(dest_matches[0] if dest_matches else "No selected match yet")

    db = EVDatabase()
    decision_agent = DecisionAgent(db)
    should_run = run
    if should_run:
        if start_location is None or destination is None:
            st.error("Select both start and destination from the location suggestions before finding a route.")
            st.stop()
        st.session_state.summary = decision_agent.decide(
            start=start_location,
            destination=destination,
            current_soc_pct=soc,
            vehicle_speed_kmh=speed,
            road_gradient_pct=gradient,
            when=datetime.now(),
        )
        st.session_state.last_soc = soc
        st.session_state.last_gradient = gradient
        st.session_state.route_confirmed = False
        st.session_state.travel_started = False
        st.session_state.show_alternatives = False
        st.session_state.alternative_index = 0
        st.session_state.confirmed_route_option = ""
        st.session_state.route_comparison_choice = ""

    if "summary" not in st.session_state:
        st.info("Enter a start location and destination, select matches from the dropdowns, then click Find Best Route.")
        st.stop()

    base_summary: DecisionSummary = st.session_state.summary
    summary: DecisionSummary = selected_decision_summary(base_summary)
    current_soc = st.session_state.get("last_soc", soc)
    road_gradient = st.session_state.get("last_gradient", gradient)

    render_hero(summary, current_soc)
    render_route_source_warning(summary)
    render_kpi_cards(summary)
    st.write("")
    render_weather_row(summary)

    st.write("")
    render_map(summary, base_summary)

    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        render_route_comparison(summary)
        render_route_details(summary)
        render_solar_roof_impact(summary)
        render_route_conditions(summary)
    with right:
        render_ai_route_decision(summary)
        render_travel_controls(summary)
        render_compact_solar_outcome(summary)
        render_risk_score(summary)
        render_departure_optimizer(summary)
        render_live_rerouting(summary)
        if summary.charging.required:
            render_charging(summary)

    with st.expander("Navigation and Operations"):
        render_turn_by_turn(summary)
        render_timeline(summary)
        render_charging_layer(summary)
    render_advanced(summary, road_gradient)


if __name__ == "__main__":
    main()
