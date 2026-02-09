"""
Pydantic schemas for device data responses.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LocationSchema(BaseModel):
    """Schema for device location"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DeviceResponse(BaseModel):
    """Schema for device data in API responses"""
    device_id: str
    location: Optional[LocationSchema] = None
    battery_level: int
    fill_level: int
    connected: bool
    last_update: str  # ISO format datetime string


class DeviceEvent(BaseModel):
    """Schema for WebSocket device events"""
    event: str  # "device_added", "device_updated", "device_disconnected"
    device: DeviceResponse
