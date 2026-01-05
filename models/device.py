"""
Device data model for IoT devices
"""
from datetime import datetime
from typing import Optional, Tuple, Dict


class Device:
    """Represents an IoT device with location, battery, and empty level data"""
    
    def __init__(self, device_id: str, location: Optional[Dict] = None, 
                 battery_level: int = 0, empty_level: int = 0):
        """
        Initialize a device
        
        Args:
            device_id: Unique identifier for the device
            location: Dictionary with 'latitude' and 'longitude' keys, or None
            battery_level: Battery level percentage (0-100)
            empty_level: Empty level percentage (0-100)
        """
        self.device_id = device_id
        self._location = location
        self.battery_level = max(0, min(100, battery_level))  # Clamp to 0-100
        self.empty_level = max(0, min(100, empty_level))  # Clamp to 0-100
        self.last_update = datetime.now()
        self.connected = True  # Device connection status
    
    @property
    def location(self) -> Optional[Tuple[float, float]]:
        """
        Get location as a tuple (latitude, longitude)
        
        Returns:
            Tuple of (latitude, longitude) or None if not set
        """
        if self._location is None:
            return None
        if isinstance(self._location, dict):
            lat = self._location.get('latitude')
            lon = self._location.get('longitude')
            if lat is not None and lon is not None:
                return (float(lat), float(lon))
        return None
    
    @location.setter
    def location(self, value: Optional[Dict]):
        """Set location from dictionary or tuple"""
        if value is None:
            self._location = None
        elif isinstance(value, dict):
            self._location = value
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            self._location = {'latitude': float(value[0]), 'longitude': float(value[1])}
    
    def update(self, location: Optional[Dict] = None, 
               battery_level: Optional[int] = None, 
               empty_level: Optional[int] = None):
        """
        Update device data
        
        Args:
            location: New location dictionary
            battery_level: New battery level
            empty_level: New empty level
        """
        if location is not None:
            self.location = location
        if battery_level is not None:
            self.battery_level = max(0, min(100, battery_level))
        if empty_level is not None:
            self.empty_level = max(0, min(100, empty_level))
        self.last_update = datetime.now()
        self.connected = True  # Mark as connected when updated
    
    def mark_disconnected(self):
        """Mark device as disconnected (but keep its data)"""
        self.connected = False
    
    def is_timed_out(self, timeout_seconds: int = 3600) -> bool:
        """
        Check if device has timed out (no update for specified seconds)
        
        Args:
            timeout_seconds: Timeout in seconds (default: 3600 = 1 hour)
            
        Returns:
            True if device has timed out
        """
        time_since_update = (datetime.now() - self.last_update).total_seconds()
        return time_since_update > timeout_seconds
    
    def to_dict(self) -> Dict:
        """Convert device to dictionary"""
        loc = self.location
        return {
            'device_id': self.device_id,
            'location': {
                'latitude': loc[0] if loc else None,
                'longitude': loc[1] if loc else None
            } if loc else None,
            'battery_level': self.battery_level,
            'empty_level': self.empty_level,
            'last_update': self.last_update.isoformat()
        }
    
    def __repr__(self) -> str:
        return f"Device(id={self.device_id}, battery={self.battery_level}%, empty={self.empty_level}%)"

