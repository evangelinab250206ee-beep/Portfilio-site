"""Example: run Phase 3 directly from Phase 2 solar results."""
from ev_energy_predictor import load_solar_results, predict_trip_energy, save_results

route_points = load_solar_results("../Solar_EV_Energy/output/solar_ev_results.csv")
results, summary = predict_trip_energy(route_points)
save_results(results, summary, "output")

print("Energy Consumed (kWh):", summary["energy_consumed_kwh"])
print("Battery Remaining (%):", summary["battery_remaining_percent"])
print("Estimated Remaining Range (km):", summary["remaining_range_km"])
