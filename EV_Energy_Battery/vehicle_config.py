"""Default Phase 3 EV parameters. Values may be overridden in code or CLI."""

vehicle_mass_kg = 1500.0
battery_capacity_kwh = 60.0
drag_coefficient = 0.24
frontal_area_m2 = 2.2
rolling_resistance_coefficient = 0.010
drivetrain_efficiency = 0.90
air_density_kg_m3 = 1.225
initial_battery_percent = 100.0

# A small HVAC / battery-conditioning correction driven by ambient temperature.
temperature_reference_c = 22.0
temperature_penalty_per_c = 0.010
