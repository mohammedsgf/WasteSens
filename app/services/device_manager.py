"""
Device Manager service for tracking IoT devices and broadcasting updates via WebSocket.
Devices are scoped per user: each user only sees their own devices.
"""
import json
import asyncio
import logging
import threading
from collections import defaultdict
from typing import Dict, Optional, List, Set
from datetime import datetime
from fastapi import WebSocket
from app.models.device import Device
from app.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections grouped by user ID."""

    def __init__(self):
        self.connections_by_user: Dict[int, Set[WebSocket]] = defaultdict(set)
        self._lock = threading.Lock()

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a new WebSocket connection and associate it with a user."""
        await websocket.accept()
        with self._lock:
            self.connections_by_user[user_id].add(websocket)
        total = sum(len(s) for s in self.connections_by_user.values())
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {total}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection for a user."""
        with self._lock:
            self.connections_by_user[user_id].discard(websocket)
            # Clean up empty sets
            if not self.connections_by_user[user_id]:
                del self.connections_by_user[user_id]
        total = sum(len(s) for s in self.connections_by_user.values())
        logger.info(f"WebSocket disconnected for user {user_id}. Total connections: {total}")

    async def broadcast_to_user(self, user_id: int, message: dict):
        """Send a JSON message only to WebSocket connections belonging to a specific user."""
        data = json.dumps(message)
        with self._lock:
            connections = list(self.connections_by_user.get(user_id, set()))
        disconnected = set()
        for ws in connections:
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.add(ws)
        # Clean up broken connections
        if disconnected:
            with self._lock:
                for ws in disconnected:
                    self.connections_by_user[user_id].discard(ws)
                if not self.connections_by_user.get(user_id):
                    self.connections_by_user.pop(user_id, None)

    async def broadcast(self, message: dict):
        """Broadcast a JSON message to ALL connected WebSocket clients (global)."""
        data = json.dumps(message)
        with self._lock:
            all_connections = [
                ws for conns in self.connections_by_user.values() for ws in conns
            ]
        disconnected_pairs: List[tuple] = []
        for ws in all_connections:
            try:
                await ws.send_text(data)
            except Exception:
                # Find which user this ws belongs to for cleanup
                with self._lock:
                    for uid, conns in self.connections_by_user.items():
                        if ws in conns:
                            disconnected_pairs.append((uid, ws))
                            break
        if disconnected_pairs:
            with self._lock:
                for uid, ws in disconnected_pairs:
                    self.connections_by_user.get(uid, set()).discard(ws)


class DeviceManager:
    """Manages multiple device instances keyed by (owner_id, device_id).
    Checks timeouts and broadcasts updates scoped to each user."""

    def __init__(self):
        # devices[owner_id][device_id] = Device
        self.devices: Dict[int, Dict[str, Device]] = defaultdict(dict)
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
        """Check for devices that have timed out and broadcast disconnection events per user."""
        for owner_id, user_devices in list(self.devices.items()):
            for device_id, device in list(user_devices.items()):
                if device.is_timed_out(settings.DEVICE_TIMEOUT_SECONDS):
                    if device.connected:
                        device.mark_disconnected()
                        logger.info(f"Device {device_id} (owner {owner_id}) timed out")
                        self._schedule_broadcast_to_user(
                            owner_id,
                            {"event": "device_disconnected", "device": device.to_dict()},
                        )

    def process_mqtt_message(self, topic: str, payload: dict):
        """
        Process an MQTT message and update/create a device.
        Topic format: smartwaste/{user_id}/{device_id}/data
        Called from the MQTT thread -- schedules async broadcast on the event loop.
        """
        try:
            parts = topic.split("/")
            # Expected: ["smartwaste", "<user_id>", "<device_id>", "data"]
            if len(parts) < 4:
                logger.warning(f"Invalid topic format (expected smartwaste/user_id/device_id/data): {topic}")
                return

            try:
                owner_id = int(parts[1])
            except (ValueError, IndexError):
                logger.warning(f"Could not parse user_id from topic: {topic}")
                return

            device_id = payload.get("device_id") or parts[2]

            location = payload.get("location")
            battery_level = payload.get("battery_level", 0)
            fill_level = payload.get("fill_level", 0)

            user_devices = self.devices[owner_id]

            if device_id in user_devices:
                device = user_devices[device_id]
                device.update(
                    location=location,
                    battery_level=battery_level,
                    fill_level=fill_level,
                )
                event = "device_updated"
                logger.debug(f"Updated device: {device_id} (owner {owner_id})")
            else:
                device = Device(
                    device_id=device_id,
                    owner_id=owner_id,
                    location=location,
                    battery_level=battery_level,
                    fill_level=fill_level,
                )
                user_devices[device_id] = device
                event = "device_added"
                logger.info(f"Added new device: {device_id} (owner {owner_id})")

            self._schedule_broadcast_to_user(
                owner_id, {"event": event, "device": device.to_dict()}
            )

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _schedule_broadcast_to_user(self, user_id: int, message: dict):
        """Schedule an async per-user broadcast from a synchronous context (MQTT thread)."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.ws_manager.broadcast_to_user(user_id, message), self._loop
            )

    def _schedule_broadcast(self, message: dict):
        """Schedule an async global broadcast from a synchronous context (MQTT thread)."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.ws_manager.broadcast(message), self._loop
            )

    def get_devices_for_user(self, user_id: int) -> List[Device]:
        """Get all devices belonging to a specific user."""
        return list(self.devices.get(user_id, {}).values())

    def get_device(self, user_id: int, device_id: str) -> Optional[Device]:
        """Get a specific device scoped to a user."""
        return self.devices.get(user_id, {}).get(device_id)

    def get_device_count(self, user_id: Optional[int] = None) -> int:
        """Get the number of tracked devices, optionally filtered by user."""
        if user_id is not None:
            return len(self.devices.get(user_id, {}))
        return sum(len(d) for d in self.devices.values())


# Singleton instances used across the application
device_manager = DeviceManager()
