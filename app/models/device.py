"""
Device data model for IoT devices (in-memory, no database persistence).
"""
from datetime import datetime
from typing import Optional, Tuple, Dict


class Device:
    """Represents an IoT device with location, battery, and fill level data"""

    def __init__(
        self,
        device_id: str,
        location: Optional[Dict] = None,
        battery_level: int = 0,
        fill_level: int = 0,
    ):
        """
        Initialize a device.

        Args:
            device_id: Unique identifier for the device.
            location: Dictionary with 'latitude' and 'longitude' keys, or None.
            battery_level: Battery level percentage (0-100).
            fill_level: Fill level percentage (0-100).
        """
        self.device_id = device_id
        self._location = location
        self.battery_level = max(0, min(100, battery_level))
        self.fill_level = max(0, min(100, fill_level))
        self.last_update = datetime.now()
        self.connected = True

    @property
    def location(self) -> Optional[Tuple[float, float]]:
        """Get location as a tuple (latitude, longitude)."""
        if self._location is None:
            return None
        if isinstance(self._location, dict):
            lat = self._location.get("latitude")
            lon = self._location.get("longitude")
            if lat is not None and lon is not None:
                return (float(lat), float(lon))
        return None

    @location.setter
    def location(self, value: Optional[Dict]):
        """Set location from dictionary or tuple."""
        if value is None:
            self._location = None
        elif isinstance(value, dict):
            self._location = value
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            self._location = {"latitude": float(value[0]), "longitude": float(value[1])}

    def update(
        self,
        location: Optional[Dict] = None,
        battery_level: Optional[int] = None,
        fill_level: Optional[int] = None,
    ):
        """Update device data."""
        if location is not None:
            self.location = location
        if battery_level is not None:
            self.battery_level = max(0, min(100, battery_level))
        if fill_level is not None:
            self.fill_level = max(0, min(100, fill_level))
        self.last_update = datetime.now()
        self.connected = True

    def mark_disconnected(self):
        """Mark device as disconnected (but keep its data)."""
        self.connected = False

    def is_timed_out(self, timeout_seconds: int = 3600) -> bool:
        """Check if device has timed out (no update for specified seconds)."""
        time_since_update = (datetime.now() - self.last_update).total_seconds()
        return time_since_update > timeout_seconds

    def to_dict(self) -> Dict:
        """Convert device to dictionary for JSON serialization."""
        loc = self.location
        return {
            "device_id": self.device_id,
            "location": {
                "latitude": loc[0] if loc else None,
                "longitude": loc[1] if loc else None,
            }
            if loc
            else None,
            "battery_level": self.battery_level,
            "fill_level": self.fill_level,
            "connected": self.connected,
            "last_update": self.last_update.isoformat(),
        }

    def __repr__(self) -> str:
        return f"Device(id={self.device_id}, battery={self.battery_level}%, fill={self.fill_level}%)"
