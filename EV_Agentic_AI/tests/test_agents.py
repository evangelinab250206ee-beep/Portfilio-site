from datetime import datetime
import unittest

from agents.decision_agent import DecisionAgent
from agents.energy_agent import EnergyAgent
from agents.weather_agent import WeatherAgent
from utils.sensors import parse_sensor_line
from utils.types import Location


class AgentTests(unittest.TestCase):
    def test_energy_prediction_positive(self):
        prediction = EnergyAgent().predict(55, 80, 2, 30, 25)
        self.assertGreater(prediction.consumption_kwh_per_100km, 0)
        self.assertGreater(prediction.remaining_range_km, 0)
        self.assertGreater(prediction.energy_required_kwh, 0)

    def test_weather_prediction_has_expected_bounds(self):
        prediction = WeatherAgent().predict(Location(12.9716, 77.5946), datetime(2026, 6, 23, 14))
        self.assertGreaterEqual(prediction.rain_probability_pct, 0)
        self.assertLessEqual(prediction.rain_probability_pct, 100)
        self.assertGreaterEqual(prediction.cloud_cover_pct, 0)
        self.assertLessEqual(prediction.cloud_cover_pct, 100)

    def test_decision_agent_produces_route(self):
        summary = DecisionAgent().decide(Location(12.9716, 77.5946), Location(13.0358, 77.5970), 75)
        self.assertGreater(summary.route.distance_km, 0)
        self.assertGreater(summary.energy.energy_required_kwh, 0)
        self.assertIn(summary.weather_risk, {"Low", "Moderate", "High"})
        self.assertGreaterEqual(len(summary.route.traffic_segments), 1)
        self.assertGreaterEqual(len(summary.route.waypoints), 2)
        self.assertGreaterEqual(len(summary.route.steps), 1)
        self.assertGreaterEqual(len(summary.route.traffic_segments[0].path), 2)
        self.assertGreaterEqual(len(summary.route_alternatives), 4)
        self.assertIn("Fastest Route", {route.route_name for route in summary.route_alternatives})
        self.assertIn("Maximum Solar Gain Route", {route.route_name for route in summary.route_alternatives})

    def test_solar_aware_route_options_exist(self):
        try:
            from dashboard.app import best_route_option, route_options
        except ModuleNotFoundError as exc:
            self.skipTest(f"Dashboard dependency not installed: {exc}")
        summary = DecisionAgent().decide(Location(12.9716, 77.5946), Location(13.0358, 77.5970), 75)
        options = route_options(summary)
        names = {option["name"] for option in options}
        self.assertIn("Maximum Solar Gain Route", names)
        for option in options:
            self.assertIn("solar_score", option)
            self.assertIn("cloud", option)
            self.assertIn("rain", option)
            self.assertGreaterEqual(option["solar"], 0)
        self.assertIn(best_route_option(summary)["name"], names)

    def test_parse_sensor_json_line(self):
        reading = parse_sensor_line(
            '{"lat":12.97,"lon":77.59,"temperature":30,"humidity":60,"voltage":360,"current":18,"speed":42,"soc":71}'
        )
        self.assertEqual(reading.location.latitude, 12.97)
        self.assertEqual(reading.battery_soc_pct, 71)

    def test_parse_sensor_csv_line(self):
        reading = parse_sensor_line("12.97,77.59,30,60,360,18,42,71")
        self.assertEqual(reading.vehicle_speed_kmh, 42)
