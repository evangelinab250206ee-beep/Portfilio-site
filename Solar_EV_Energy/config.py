"""Default solar-panel settings for the EV roof installation."""

panel_area = 2.0
panel_efficiency = 0.22
mppt_efficiency = 0.95
temperature_coefficient = -0.004

# Roof-mounted panel orientation. 0° tilt is horizontal; azimuth is clockwise
# from north (180° = south-facing in the northern hemisphere).
tilt_angle = 0.0
azimuth_angle = 180.0

# Typical fixed-panel assumptions used to estimate cell temperature and POA.
nominal_operating_cell_temperature = 45.0
ground_albedo = 0.20
cloud_cover_loss_strength = 0.65
