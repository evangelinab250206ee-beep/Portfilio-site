"""ESP32/Arduino serial sensor integration."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable

from config.settings import settings
from utils.types import Location, SensorReading


class SerialSensorReader:
    """Read EV sensor packets from a serial port.

    Supported formats:
    JSON line:
      {"lat":12.97,"lon":77.59,"temperature":30,"humidity":60,"voltage":360,"current":18,"speed":42,"soc":71}

    CSV line:
      lat,lon,temperature,humidity,voltage,current,speed,soc
    """

    def __init__(self, port: str = settings.serial_port, baudrate: int = settings.serial_baudrate, timeout: float = 2.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def read_once(self) -> SensorReading:
        try:
            import serial
        except Exception as exc:  # pragma: no cover - optional hardware dependency
            raise RuntimeError("pyserial is required for ESP32/Arduino input.") from exc
        with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as device:
            line = device.readline().decode("utf-8", errors="replace").strip()
        if not line:
            raise TimeoutError(f"No sensor data received on {self.port}.")
        return parse_sensor_line(line)


def parse_sensor_line(line: str) -> SensorReading:
    if line.lstrip().startswith("{"):
        payload = json.loads(line)
        values = {
            "lat": payload.get("lat", payload.get("latitude")),
            "lon": payload.get("lon", payload.get("longitude")),
            "temperature": payload.get("temperature", payload.get("temperature_c")),
            "humidity": payload.get("humidity", payload.get("humidity_pct")),
            "voltage": payload.get("voltage", payload.get("battery_voltage_v")),
            "current": payload.get("current", payload.get("battery_current_a")),
            "speed": payload.get("speed", payload.get("vehicle_speed_kmh")),
            "soc": payload.get("soc", payload.get("battery_soc_pct")),
        }
    else:
        values = _parse_csv_values(line.split(","))
    return SensorReading(
        timestamp=datetime.now(),
        location=Location(float(values["lat"]), float(values["lon"]), "sensor"),
        temperature_c=float(values["temperature"]),
        humidity_pct=float(values["humidity"]),
        battery_voltage_v=float(values["voltage"]),
        battery_current_a=float(values["current"]),
        vehicle_speed_kmh=float(values["speed"]),
        battery_soc_pct=float(values["soc"]),
    )


def _parse_csv_values(parts: Iterable[str]) -> dict[str, float]:
    fields = ["lat", "lon", "temperature", "humidity", "voltage", "current", "speed", "soc"]
    clean = [part.strip() for part in parts]
    if len(clean) != len(fields):
        raise ValueError(f"Expected {len(fields)} CSV fields, got {len(clean)}.")
    return dict(zip(fields, map(float, clean)))
