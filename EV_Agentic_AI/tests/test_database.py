from datetime import datetime
import unittest

from database.db import EVDatabase
from utils.types import Location, SensorReading


class DatabaseTests(unittest.TestCase):
    def test_database_logs_sensor_reading(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as tmp_dir:
            db = EVDatabase(Path(tmp_dir) / "test.sqlite3")
            db.log_sensor_reading(
                SensorReading(
                    timestamp=datetime.now(),
                    location=Location(1.0, 2.0),
                    temperature_c=25,
                    humidity_pct=50,
                    battery_voltage_v=350,
                    battery_current_a=10,
                    vehicle_speed_kmh=40,
                    battery_soc_pct=80,
                )
            )
            rows = db.latest_rows("sensor_logs", 1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["battery_soc_pct"], 80)
