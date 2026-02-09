"""
Device Manager service for tracking IoT devices and broadcasting updates via WebSocket.
"""
import json
import asyncio
import logging
import threading
from typing import Dict, Optional, List, Set
from datetime import datetime
from fastapi import WebSocket
from app.models.device import Device
from app.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a JSON message to all connected WebSocket clients."""
        data = json.dumps(message)
        disconnected = set()
        for ws in list(self.active_connections):
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.add(ws)
        # Clean up broken connections
        if disconnected:
            with self._lock:
                self.active_connections -= disconnected


class DeviceManager:
    """Manages multiple device instances, checks timeouts, and broadcasts updates."""

    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.ws_manager = ConnectionManager()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._timeout_task: Optional[asyncio.Task] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the asyncio event loop for scheduling broadcasts from sync MQTT callbacks."""
        self._loop = loop

    async def start_timeout_checker(self):
        """Background task that periodically checks for timed-out devices."""
        while True:
            await asyncio.sleep(60)
            self._check_timeouts()

    def _check_timeouts(self):
        """Check for devices that have timed out and broadcast disconnection events."""
        for device_id, device in list(self.devices.items()):
            if device.is_timed_out(settings.DEVICE_TIMEOUT_SECONDS):
                if device.connected:
                    device.mark_disconnected()
                    logger.info(f"Device {device_id} timed out")
                    self._schedule_broadcast(
                        {"event": "device_disconnected", "device": device.to_dict()}
                    )

    def process_mqtt_message(self, topic: str, payload: dict):
        """
        Process an MQTT message and update/create a device.
        Called from the MQTT thread -- schedules async broadcast on the event loop.
        """
        try:
            device_id = payload.get("device_id")
            if not device_id:
                parts = topic.split("/")
                if len(parts) >= 2:
                    device_id = parts[1]
                else:
                    logger.warning(f"Could not determine device_id from topic: {topic}")
                    return

            location = payload.get("location")
            battery_level = payload.get("battery_level", 0)
            fill_level = payload.get("fill_level", 0)

            if device_id in self.devices:
                device = self.devices[device_id]
                device.update(
                    location=location,
                    battery_level=battery_level,
                    fill_level=fill_level,
                )
                event = "device_updated"
                logger.debug(f"Updated device: {device_id}")
            else:
                device = Device(
                    device_id=device_id,
                    location=location,
                    battery_level=battery_level,
                    fill_level=fill_level,
                )
                self.devices[device_id] = device
                event = "device_added"
                logger.info(f"Added new device: {device_id}")

            self._schedule_broadcast({"event": event, "device": device.to_dict()})

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _schedule_broadcast(self, message: dict):
        """Schedule an async broadcast from a synchronous context (MQTT thread)."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.ws_manager.broadcast(message), self._loop
            )

    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        return self.devices.get(device_id)

    def get_all_devices(self) -> List[Device]:
        """Get all devices."""
        return list(self.devices.values())

    def get_device_count(self) -> int:
        """Get the number of tracked devices."""
        return len(self.devices)


# Singleton instances used across the application
device_manager = DeviceManager()
