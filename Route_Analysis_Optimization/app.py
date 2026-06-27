"""Streamlit engineering dashboard for Solar-Assisted EV Route Optimisation.

Run from this folder:
    streamlit run app.py
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from report_export import create_pdf_report
from route_optimizer import RouteOptimizer, VehicleConfig
from route_service import generate_route_alternatives, geocode_city, write_routes_to_gpx

# Imported after route_optimizer configures the paths to existing project phases.
from solar_ev_predictor import PanelConfig

APP_DIR = Path(__file__).resolve().parent
RUNS_DIR = APP_DIR / "dashboard_runs"

st.set_page_config(page_title="Solar-Assisted EV Route Optimiser", page_icon="⚡", layout="wide")


@st.cache_data(ttl=86_400, show_spinner=False)
def cached_geocode(city: str) -> dict:
    return geocode_city(city)


@st.cache_data(ttl=21_600, show_spinner=False)
def cached_routes(start: str, destination: str) -> list[dict]:
    return generate_route_alternatives(cached_geocode(start), cached_geocode(destination), alternatives=3)


def _safe_run_key(values: dict) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _route_key(label: str) -> str:
    return label.lower().replace(" ", "_")


def _run_analysis(values: dict) -> dict:
    """Generate road routes, orchestrate the existing modules, and return file paths."""
    routes = cached_routes(values["start_city"], values["destination_city"])
    run_dir = RUNS_DIR / _safe_run_key(values)
    gpx_dir, output_dir = run_dir / "gpx", run_dir / "output"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    write_routes_to_gpx(routes, gpx_dir)
    panel = PanelConfig(
        panel_area_m2=values["panel_area"],
        panel_efficiency=values["panel_efficiency"] / 100,
    )
    vehicle = VehicleConfig(
        vehicle_mass_kg=values["vehicle_mass"],
        battery_capacity_kwh=values["battery_capacity"],
    )
    optimizer = RouteOptimizer(
        departure_date=values["departure_date"].isoformat(),
        departure_time=values["departure_time"].strftime("%H:%M"),
        travel_speed_kmh=values["speed_kmh"],
        vehicle=vehicle,
        panel_config=panel,
        sample_distance_km=values["sample_distance_km"],
        scoring_weights=values["weights"],
    )
    comparison = optimizer.process_routes(gpx_dir, output_dir)
    recommendation = json.loads((output_dir / "best_route.json").read_text(encoding="utf-8"))
    pdf_path = create_pdf_report(comparison, recommendation, output_dir / "route_summary.pdf")
    return {
        "routes": routes, "comparison": comparison, "recommendation": recommendation,
        "output_dir": str(output_dir), "pdf_path": str(pdf_path),
    }


def _read_route_results(result: dict, route: str) -> pd.DataFrame:
    return pd.read_csv(Path(result["output_dir"]) / f"{route}_results.csv")


def _build_map(routes: list[dict], recommendation: dict, start: dict, destination: dict):
    center = [(start["latitude"] + destination["latitude"]) / 2, (start["longitude"] + destination["longitude"]) / 2]
    route_map = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")
    colors = ["#2563eb", "#16a34a", "#f97316"]
    best = recommendation["best_route"]
    for index, route in enumerate(routes):
        is_best = _route_key(route["route"]) == best
        folium.PolyLine(
            route["coordinates"], color="#dc2626" if is_best else colors[index % len(colors)],
            weight=7 if is_best else 4, opacity=0.9,
            popup=f"{route['route']}<br>{route['distance_km']} km<br>{route['duration_hours']} h" + ("<br><b>Recommended</b>" if is_best else ""),
        ).add_to(route_map)
    folium.Marker([start["latitude"], start["longitude"]], popup=f"Start: {start['label']}", icon=folium.Icon(color="green", icon="play")).add_to(route_map)
    folium.Marker([destination["latitude"], destination["longitude"]], popup=f"Destination: {destination['label']}", icon=folium.Icon(color="red", icon="flag")).add_to(route_map)
    return route_map


def _line_chart(frame: pd.DataFrame, y: str, title: str, y_label: str):
    return px.line(frame, x="cumulative_distance_km", y=y, markers=True, title=title, labels={"cumulative_distance_km": "Distance (km)", y: y_label})


def main() -> None:
    st.markdown("""<style>
    .hero {padding: 0.8rem 0 0.2rem 0;} .hero h1 {color:#0f172a; margin-bottom:0.2rem;}
    div[data-testid="stMetric"] {background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:0.7rem;}
    </style>""", unsafe_allow_html=True)
    st.markdown("<div class='hero'><h1>⚡ Solar-Assisted EV Route Optimisation</h1><p>Weather-aware solar generation, battery prediction, and route ranking for engineering analysis.</p></div>", unsafe_allow_html=True)

    system_now = datetime.now().astimezone().replace(second=0, microsecond=0)
    with st.sidebar:
        st.header("Route inputs")
        start_city = st.text_input("Start City", value="Kochi, Kerala, India")
        destination_city = st.text_input("Destination City", value="Bengaluru, Karnataka, India")
        use_current = st.checkbox("Use Current Date & Time", value=True)
        if use_current:
            departure_date, departure_time = system_now.date(), system_now.time()
            st.caption("The system date and time are used at the moment of analysis.")
        else:
            departure_date = st.date_input("Departure Date", value=system_now.date())
            departure_time = st.time_input("Departure Time", value=system_now.time())

        st.header("Vehicle & solar panel")
        battery_capacity = st.number_input("Battery Capacity (kWh)", min_value=10.0, value=60.0, step=1.0)
        vehicle_mass = st.number_input("Vehicle Mass (kg)", min_value=500.0, value=1500.0, step=50.0)
        panel_area = st.number_input("Solar Panel Area (m²)", min_value=0.1, value=2.0, step=0.1)
        panel_efficiency = st.slider("Panel Efficiency (%)", min_value=5.0, max_value=35.0, value=22.0, step=0.5)

        st.header("Advanced settings")
        speed_kmh = st.number_input("Average Speed (km/h)", min_value=10.0, max_value=130.0, value=55.0, step=5.0)
        sample_distance_km = st.slider("Route Sampling Distance (km)", min_value=2.0, max_value=25.0, value=10.0, step=1.0)
        with st.expander("Route scoring weights"):
            battery_weight = st.slider("Battery reserve", 0.0, 1.0, 0.50, 0.05)
            solar_weight = st.slider("Solar gain", 0.0, 1.0, 0.25, 0.05)
            travel_weight = st.slider("Travel time", 0.0, 1.0, 0.15, 0.05)
            weather_weight = st.slider("Weather safety", 0.0, 1.0, 0.10, 0.05)
            st.caption(f"Weight total: {battery_weight + solar_weight + travel_weight + weather_weight:.2f}")
        analyze_clicked = st.button("Analyze Routes", type="primary", use_container_width=True)

    departure_datetime = datetime.combine(departure_date, departure_time)
    current_col, time_col, used_col = st.columns(3)
    current_col.metric("Current Date", system_now.strftime("%d %b %Y"))
    time_col.metric("Current Time", system_now.strftime("%H:%M %Z"))
    used_col.metric("Departure Time Used", departure_datetime.strftime("%d %b %Y, %H:%M"))

    values = {
        "start_city": start_city.strip(), "destination_city": destination_city.strip(),
        "departure_date": departure_date, "departure_time": departure_time,
        "battery_capacity": battery_capacity, "vehicle_mass": vehicle_mass,
        "panel_area": panel_area, "panel_efficiency": panel_efficiency,
        "speed_kmh": speed_kmh, "sample_distance_km": sample_distance_km,
        "weights": {"battery": battery_weight, "solar": solar_weight, "travel_time": travel_weight, "weather": weather_weight},
    }
    fingerprint = _safe_run_key(values)
    automatic_recalculation = st.session_state.get("analysis") is not None and st.session_state.get("analysis_fingerprint") != fingerprint
    if analyze_clicked or automatic_recalculation:
        if not values["start_city"] or not values["destination_city"]:
            st.error("Enter both a start city and destination city.")
        else:
            try:
                with st.spinner("Generating routes and running weather, solar, EV, and optimisation models…"):
                    st.session_state.analysis = _run_analysis(values)
                    st.session_state.analysis_fingerprint = fingerprint
                st.success("Route analysis complete.")
            except Exception as error:
                st.error(f"Route analysis could not be completed: {error}")
                st.info("Check city spelling, internet access for map/elevation services, and that the existing model dependencies and files are installed.")

    result = st.session_state.get("analysis")
    if result is None:
        st.info("Set the inputs and select **Analyze Routes** to generate three alternatives and the full EV analysis.")
        return

    comparison = result["comparison"]
    recommendation = result["recommendation"]
    start, destination = cached_geocode(values["start_city"]), cached_geocode(values["destination_city"])
    st.divider()
    st.subheader("Recommended Route")
    metric_a, metric_b, metric_c, metric_d = st.columns(4)
    metric_a.metric("Best Route", recommendation["best_route"].replace("_", " ").title())
    metric_b.metric("Battery Remaining", f"{recommendation['expected_battery_remaining_percent']:.1f}%")
    metric_c.metric("Solar Gain", f"{recommendation['expected_solar_gain_kwh']:.2f} kWh")
    metric_d.metric("Travel Time", f"{recommendation['expected_travel_time_hours']:.2f} h")
    st.success(recommendation["reason"])
    st.caption(f"Expected weather condition: average risk score {recommendation['expected_weather_conditions']['average_weather_risk']:.2f} (0 = low risk, 1 = high risk).")

    map_col, table_col = st.columns([1.25, 1])
    with map_col:
        st.subheader("Route Map")
        st_folium(_build_map(result["routes"], recommendation, start, destination), height=480, use_container_width=True, key="route-map")
    with table_col:
        st.subheader("Route Comparison")
        table_columns = ["route", "total_distance_km", "estimated_travel_time_hours", "total_solar_energy_kwh", "total_energy_consumed_kwh", "final_battery_remaining_percent", "average_weather_risk", "route_score"]
        st.dataframe(comparison[table_columns], use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(comparison, x="route", y="route_score", color="route", title="Route Comparison Dashboard"), use_container_width=True)

    st.subheader("Route Detail Analysis")
    selected_route = st.selectbox("Select route", comparison["route"].tolist(), format_func=lambda value: value.replace("_", " ").title())
    frame = _read_route_results(result, selected_route)
    tab_battery, tab_solar, tab_elevation, tab_weather, tab_energy = st.tabs(["Battery", "Solar", "Elevation", "Weather", "Energy"])
    with tab_battery:
        st.plotly_chart(_line_chart(frame, "battery_remaining_percent", "Battery Remaining vs Distance", "Battery Remaining (%)"), use_container_width=True)
    with tab_solar:
        st.plotly_chart(_line_chart(frame, "cumulative_solar_energy_wh", "Solar Energy vs Distance", "Cumulative Solar Energy (Wh)"), use_container_width=True)
    with tab_elevation:
        st.plotly_chart(_line_chart(frame, "elevation_m", "Elevation vs Distance", "Elevation (m)"), use_container_width=True)
    with tab_weather:
        weather_figure = go.Figure()
        weather_figure.add_scatter(x=frame["cumulative_distance_km"], y=frame["temperature"], name="Temperature (°C)")
        weather_figure.add_scatter(x=frame["cumulative_distance_km"], y=frame["cloud_cover"], name="Cloud Cover (%)", yaxis="y2")
        weather_figure.update_layout(title="Weather Conditions vs Distance", xaxis_title="Distance (km)", yaxis_title="Temperature (°C)", yaxis2={"title": "Cloud Cover (%)", "overlaying": "y", "side": "right"})
        st.plotly_chart(weather_figure, use_container_width=True)
    with tab_energy:
        st.plotly_chart(_line_chart(frame, "energy_consumed_wh", "Energy Consumption vs Distance", "Energy Consumed (Wh)"), use_container_width=True)

    st.subheader("Exports")
    output_dir = Path(result["output_dir"])
    export_a, export_b, export_c = st.columns(3)
    export_a.download_button("Download Comparison CSV", comparison.to_csv(index=False).encode("utf-8"), "route_comparison.csv", "text/csv", use_container_width=True)
    export_b.download_button("Download Recommendation JSON", (output_dir / "best_route.json").read_bytes(), "best_route.json", "application/json", use_container_width=True)
    export_c.download_button("Download PDF Report", Path(result["pdf_path"]).read_bytes(), "route_summary.pdf", "application/pdf", use_container_width=True)


if __name__ == "__main__":
    main()
