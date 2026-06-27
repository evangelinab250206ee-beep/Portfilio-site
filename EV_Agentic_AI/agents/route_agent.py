"""Route optimization agent based on OSMnx/NetworkX with a geodesic fallback."""

from __future__ import annotations

from math import ceil, sqrt

from agents.base_agent import AgentProfile, BaseEVAgent
from database.db import EVDatabase
from utils.geo import haversine_km, interpolate_path
from utils.types import Location, RoutePlan, RouteStep, RouteWaypoint, TrafficSegment, WeatherPrediction


class RouteAgent(BaseEVAgent):
    profile = AgentProfile(
        role="Route Agent",
        goal="Recommend route geometry, travel time, and route energy demand.",
        backstory="A route planner that prefers roads when OSM data is available and reliable fallback estimates otherwise.",
    )

    def __init__(self, db: EVDatabase | None = None, average_speed_kmh: float = 48.0) -> None:
        self.db = db
        self.average_speed_kmh = average_speed_kmh

    def plan(self, start: Location, destination: Location, weather: WeatherPrediction, consumption_kwh_per_100km: float) -> RoutePlan:
        route = self.plan_alternatives(start, destination, weather, consumption_kwh_per_100km)[0]
        if self.db:
            self.db.log_route(route)
        return route

    def plan_alternatives(
        self, start: Location, destination: Location, weather: WeatherPrediction, consumption_kwh_per_100km: float
    ) -> list[RoutePlan]:
        routes = self._osrm_routes(start, destination, weather, consumption_kwh_per_100km)
        if not routes:
            osmnx_route = self._osmnx_route(start, destination, weather, consumption_kwh_per_100km)
            routes = [osmnx_route] if osmnx_route else []
        if not routes:
            routes = [self._fallback_route(start, destination, weather, consumption_kwh_per_100km)]
        routes = self._ensure_candidate_routes(routes, start, destination, weather, consumption_kwh_per_100km)
        routes = self._label_routes(routes)
        if self.db:
            self.db.log_route(routes[0])
        return routes

    def _osrm_route(
        self, start: Location, destination: Location, weather: WeatherPrediction, consumption_kwh_per_100km: float
    ) -> RoutePlan | None:
        routes = self._osrm_routes(start, destination, weather, consumption_kwh_per_100km)
        return routes[0] if routes else None

    def _osrm_routes(
        self, start: Location, destination: Location, weather: WeatherPrediction, consumption_kwh_per_100km: float
    ) -> list[RoutePlan]:
        try:
            import requests

            routes: list[RoutePlan] = []
            route_specs = [
                (f"{start.longitude},{start.latitude};{destination.longitude},{destination.latitude}", "direct"),
            ]
            for via in self._via_points(start, destination):
                route_specs.append(
                    (
                        f"{start.longitude},{start.latitude};{via.longitude},{via.latitude};{destination.longitude},{destination.latitude}",
                        "via",
                    )
                )
            for coordinates_text, source_suffix in route_specs:
                response = requests.get(
                    f"https://router.project-osrm.org/route/v1/driving/{coordinates_text}",
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                        "steps": "true",
                        "alternatives": "true" if source_suffix == "direct" else "false",
                    },
                    timeout=12,
                )
                response.raise_for_status()
                for route_data in response.json().get("routes", []):
                    route = self._route_from_osrm_data(
                        start, destination, route_data, weather, consumption_kwh_per_100km, f"osrm-{source_suffix}"
                    )
                    if route and not self._is_duplicate_route(route, routes):
                        routes.append(route)
                    if len(routes) >= 5:
                        break
                if len(routes) >= 5:
                    break
            return routes
        except Exception:
            return []

    def _route_from_osrm_data(
        self,
        start: Location,
        destination: Location,
        route_data: dict,
        weather: WeatherPrediction,
        consumption_kwh_per_100km: float,
        source: str,
    ) -> RoutePlan | None:
        coordinates = route_data.get("geometry", {}).get("coordinates", [])
        if len(coordinates) < 2:
            return None
        path = [Location(latitude=lat, longitude=lon, label="road") for lon, lat in coordinates]
        distance_km = float(route_data["distance"]) / 1000
        base_minutes = float(route_data["duration"]) / 60
        weather_factor = 1 + weather.rain_probability_pct / 500
        travel_time = base_minutes * weather_factor
        energy = distance_km * consumption_kwh_per_100km * weather_factor / 100
        steps = self._parse_osrm_steps(route_data, path)
        road_names = self._road_names_from_steps(steps)
        traffic_segments = self._traffic_segments(path, distance_km, travel_time, weather)
        waypoints = self._route_waypoints(start, destination, path, travel_time, weather, road_names)
        return RoutePlan(start, destination, distance_km, travel_time, path, energy, source, "OSRM Route", steps, traffic_segments, waypoints, road_names)

    def _osmnx_route(
        self, start: Location, destination: Location, weather: WeatherPrediction, consumption_kwh_per_100km: float
    ) -> RoutePlan | None:
        try:
            import networkx as nx
            import osmnx as ox

            center_lat = (start.latitude + destination.latitude) / 2
            center_lon = (start.longitude + destination.longitude) / 2
            radius_m = max(2500, haversine_km(start, destination) * 700)
            graph = ox.graph_from_point((center_lat, center_lon), dist=radius_m, network_type="drive")
            source = ox.distance.nearest_nodes(graph, start.longitude, start.latitude)
            target = ox.distance.nearest_nodes(graph, destination.longitude, destination.latitude)
            nodes = nx.shortest_path(graph, source, target, weight="length")
            distance_km = sum(ox.utils_graph.get_route_edge_attributes(graph, nodes, "length")) / 1000
            path = [Location(graph.nodes[node]["y"], graph.nodes[node]["x"], "osm-node") for node in nodes]
            weather_factor = 1 + weather.rain_probability_pct / 500
            energy = distance_km * consumption_kwh_per_100km * weather_factor / 100
            travel_time = distance_km / self.average_speed_kmh * 60 * weather_factor
            traffic_segments = self._traffic_segments(path, distance_km, travel_time, weather)
            waypoints = self._route_waypoints(start, destination, path, travel_time, weather, [])
            return RoutePlan(start, destination, distance_km, travel_time, path, energy, "osmnx", "OSMnx Route", [], traffic_segments, waypoints, [])
        except Exception:
            return None

    def _fallback_route(
        self, start: Location, destination: Location, weather: WeatherPrediction, consumption_kwh_per_100km: float
    ) -> RoutePlan:
        distance_km = haversine_km(start, destination) * 1.22
        weather_factor = 1 + weather.rain_probability_pct / 500
        travel_time = distance_km / self.average_speed_kmh * 60 * weather_factor
        energy = distance_km * consumption_kwh_per_100km * weather_factor / 100
        path = interpolate_path(start, destination)
        traffic_segments = self._traffic_segments(path, distance_km, travel_time, weather)
        waypoints = self._route_waypoints(start, destination, path, travel_time, weather, [])
        steps = [
            RouteStep("Start trip", 0.0, 0.0, start),
            RouteStep("Continue toward destination", distance_km, travel_time, path[len(path) // 2]),
            RouteStep("Arrive at destination", 0.0, 0.0, destination),
        ]
        return RoutePlan(start, destination, distance_km, travel_time, path, energy, "geodesic", "Approximate Route", steps, traffic_segments, waypoints, [])

    def _candidate_route(
        self,
        start: Location,
        destination: Location,
        via: Location,
        weather: WeatherPrediction,
        consumption_kwh_per_100km: float,
        source: str,
    ) -> RoutePlan:
        first = interpolate_path(start, via, 8)
        second = interpolate_path(via, destination, 8)[1:]
        path = first + second
        distance_km = (haversine_km(start, via) + haversine_km(via, destination)) * 1.18
        weather_factor = 1 + weather.rain_probability_pct / 500
        travel_time = distance_km / self.average_speed_kmh * 60 * weather_factor
        energy = distance_km * consumption_kwh_per_100km * weather_factor / 100
        traffic_segments = self._traffic_segments(path, distance_km, travel_time, weather)
        waypoints = self._route_waypoints(start, destination, path, travel_time, weather, [])
        steps = [
            RouteStep("Start trip", 0.0, 0.0, start),
            RouteStep("Continue via optimized candidate corridor", distance_km * 0.55, travel_time * 0.55, via),
            RouteStep("Arrive at destination", 0.0, 0.0, destination),
        ]
        return RoutePlan(start, destination, distance_km, travel_time, path, energy, source, "Candidate Route", steps, traffic_segments, waypoints, [])

    def _ensure_candidate_routes(
        self,
        routes: list[RoutePlan],
        start: Location,
        destination: Location,
        weather: WeatherPrediction,
        consumption_kwh_per_100km: float,
    ) -> list[RoutePlan]:
        candidates = list(routes)
        for index, via in enumerate(self._via_points(start, destination)):
            if len(candidates) >= 4:
                break
            route = self._candidate_route(start, destination, via, weather, consumption_kwh_per_100km, f"candidate-{index + 1}")
            if not self._is_duplicate_route(route, candidates):
                candidates.append(route)
        return candidates[:4]

    @staticmethod
    def _via_points(start: Location, destination: Location) -> list[Location]:
        mid_lat = (start.latitude + destination.latitude) / 2
        mid_lon = (start.longitude + destination.longitude) / 2
        dlat = destination.latitude - start.latitude
        dlon = destination.longitude - start.longitude
        norm = sqrt(dlat * dlat + dlon * dlon) or 1.0
        perp_lat = -dlon / norm
        perp_lon = dlat / norm
        route_span = max(abs(dlat), abs(dlon), 0.02)
        offsets = [route_span * 0.18, -route_span * 0.18, route_span * 0.32, -route_span * 0.32]
        return [Location(mid_lat + perp_lat * offset, mid_lon + perp_lon * offset, "via") for offset in offsets]

    @staticmethod
    def _is_duplicate_route(route: RoutePlan, routes: list[RoutePlan]) -> bool:
        signature = {(round(point.latitude, 4), round(point.longitude, 4)) for point in route.path[:: max(1, len(route.path) // 20)]}
        for existing in routes:
            existing_signature = {
                (round(point.latitude, 4), round(point.longitude, 4)) for point in existing.path[:: max(1, len(existing.path) // 20)]
            }
            overlap = len(signature & existing_signature) / max(1, min(len(signature), len(existing_signature)))
            if overlap > 0.82:
                return True
        return False

    @staticmethod
    def _label_routes(routes: list[RoutePlan]) -> list[RoutePlan]:
        from dataclasses import replace

        labels = ["Fastest Route", "Efficient Route", "Weather Safe Route", "Maximum Solar Gain Route"]
        sorted_routes = sorted(routes, key=lambda route: route.travel_time_min)
        labelled = []
        for index, route in enumerate(sorted_routes):
            labelled.append(replace(route, route_name=labels[min(index, len(labels) - 1)]))
        if labelled and len(labelled) < 4:
            labelled[-1] = replace(labelled[-1], route_name="Maximum Solar Gain Route")
        return labelled

    def _parse_osrm_steps(self, route_data: dict, path: list[Location]) -> list[RouteStep]:
        steps: list[RouteStep] = []
        for leg in route_data.get("legs", []):
            for step in leg.get("steps", []):
                maneuver = step.get("maneuver", {})
                location = maneuver.get("location", [path[0].longitude, path[0].latitude])
                road = step.get("name") or "road"
                instruction = self._instruction(maneuver.get("type", "continue"), maneuver.get("modifier"), road)
                steps.append(
                    RouteStep(
                        instruction=instruction,
                        distance_km=float(step.get("distance", 0)) / 1000,
                        duration_min=float(step.get("duration", 0)) / 60,
                        location=Location(float(location[1]), float(location[0]), road),
                    )
                )
        return steps[:18]

    @staticmethod
    def _instruction(action: str, modifier: str | None, road: str) -> str:
        if action == "depart":
            return f"Head {modifier or 'ahead'} on {road}"
        if action == "arrive":
            return "Arrive at destination"
        if action == "turn":
            return f"Turn {modifier or 'ahead'} onto {road}"
        if action == "merge":
            return f"Merge {modifier or 'ahead'} onto {road}"
        if action == "roundabout":
            return f"Enter roundabout toward {road}"
        if action == "fork":
            return f"Keep {modifier or 'ahead'} toward {road}"
        return f"Continue on {road}"

    @staticmethod
    def _road_names_from_steps(steps: list[RouteStep]) -> list[str]:
        names: list[str] = []
        for step in steps:
            name = step.location.label.strip()
            if name and name != "road" and name not in names:
                names.append(name)
        return names[:6]

    def _traffic_segments(
        self, path: list[Location], distance_km: float, travel_time_min: float, weather: WeatherPrediction
    ) -> list[TrafficSegment]:
        if len(path) < 2:
            return []
        segment_count = min(8, max(3, ceil(distance_km / 7)))
        stride = max(1, (len(path) - 1) // segment_count)
        segments: list[TrafficSegment] = []
        remaining_distance = distance_km
        remaining_time = travel_time_min
        statuses = self._traffic_pattern(distance_km, travel_time_min, weather)
        for index in range(segment_count):
            start_index = min(index * stride, len(path) - 2)
            end_index = len(path) - 1 if index == segment_count - 1 else min((index + 1) * stride, len(path) - 1)
            segment_distance = distance_km / segment_count
            segment_time = travel_time_min / segment_count
            remaining_distance -= segment_distance
            remaining_time -= segment_time
            segments.append(
                TrafficSegment(
                    start=path[start_index],
                    end=path[end_index],
                    status=statuses[index % len(statuses)],
                    distance_km=max(0.1, segment_distance),
                    duration_min=max(0.2, segment_time),
                    path=path[start_index : end_index + 1],
                )
            )
        return segments

    @staticmethod
    def _traffic_pattern(distance_km: float, travel_time_min: float, weather: WeatherPrediction) -> list[str]:
        minutes_per_km = travel_time_min / max(distance_km, 1)
        if weather.rain_probability_pct > 65 or minutes_per_km > 2.1:
            return ["fast", "moderate", "slow", "congested", "moderate"]
        if minutes_per_km > 1.5:
            return ["fast", "moderate", "slow", "moderate"]
        return ["fast", "fast", "moderate", "fast"]

    def _route_waypoints(
        self,
        start: Location,
        destination: Location,
        path: list[Location],
        travel_time_min: float,
        weather: WeatherPrediction,
        road_names: list[str],
    ) -> list[RouteWaypoint]:
        names = [start.label or "Start"]
        names.extend(road_names[:3] if road_names else ["Mid-route", "Approach road"])
        names.append(destination.label or "Destination")
        sample_count = len(names)
        points = [path[min(len(path) - 1, round(i * (len(path) - 1) / max(sample_count - 1, 1)))] for i in range(sample_count)]
        waypoints: list[RouteWaypoint] = []
        for index, (name, point) in enumerate(zip(names, points)):
            eta = travel_time_min * index / max(sample_count - 1, 1)
            weather_text = self._weather_text(weather, index)
            solar_text = "High solar" if weather.cloud_cover_pct < 35 else "Cloudy solar" if weather.cloud_cover_pct > 70 else "Moderate solar"
            waypoints.append(RouteWaypoint(name, point, eta, weather_text, solar_text))
        return waypoints

    @staticmethod
    def _weather_text(weather: WeatherPrediction, index: int) -> str:
        if weather.rain_probability_pct > 65 and index % 2 == 1:
            return "Light rain"
        if weather.cloud_cover_pct > 65:
            return "Cloudy"
        if weather.rain_probability_pct > 35:
            return "Partly cloudy"
        return "Sunny"
