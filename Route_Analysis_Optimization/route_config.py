"""Configuration for Phase 4 route analysis and scoring."""

sample_distance_km = 10.0
maximum_route_points = 100
default_travel_speed_kmh = 55.0

battery_weight = 0.50
solar_weight = 0.25
travel_time_weight = 0.15
weather_weight = 0.10

# Latitude/longitude rounding bounds the cache while retaining useful locality.
weather_cache_decimal_places = 2
elevation_api_batch_size = 100
