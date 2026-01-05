"""
Device Manager for tracking and managing multiple IoT devices
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from models.device import Device

logger = logging.getLogger(__name__)

# Device timeout: 1 hour
DEVICE_TIMEOUT_SECONDS = 3600


class DeviceManager(QObject):
    """Manages multiple device instances and their state"""
    
    # Signal emitted when a device is added
    # Arguments: device (Device)
    device_added = pyqtSignal(Device)
    
    # Signal emitted when a device is updated
    # Arguments: device (Device)
    device_updated = pyqtSignal(Device)
    
    # Signal emitted when a device is disconnected (timed out)
    # Arguments: device (Device)
    device_disconnected = pyqtSignal(Device)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices: Dict[str, Device] = {}
        # Setup periodic timeout check (every 60 seconds)
        self.timeout_timer = QTimer(self)
        self.timeout_timer.timeout.connect(self._check_timeouts)
        self.timeout_timer.start(60000)  # Check every minute
    
    def process_mqtt_message(self, topic: str, payload: dict):
        """
        Process an MQTT message and update/create device
        
        Args:
            topic: MQTT topic (e.g., "smartwaste/device001/data")
            payload: Parsed JSON payload containing device data
        """
        try:
            logger.info(f"Processing MQTT message - Topic: {topic}, Payload: {payload}")
            # Extract device_id from payload or topic
            device_id = payload.get('device_id')
            if not device_id:
                # Try to extract from topic if not in payload
                # Topic format: smartwaste/device001/data
                parts = topic.split('/')
                if len(parts) >= 2:
                    device_id = parts[1]
                else:
                    logger.warning(f"Could not determine device_id from topic: {topic}")
                    return
            
            # Extract device data
            location = payload.get('location')
            battery_level = payload.get('battery_level', 0)
            empty_level = payload.get('empty_level', 0)
            
            # Update or create device
            if device_id in self.devices:
                # Update existing device
                device = self.devices[device_id]
                was_disconnected = not device.connected
                device.update(
                    location=location,
                    battery_level=battery_level,
                    empty_level=empty_level
                )
                logger.debug(f"Updated device: {device_id}")
                # If device was disconnected and now reconnected, emit update
                if was_disconnected:
                    logger.info(f"Device {device_id} reconnected")
                self.device_updated.emit(device)
            else:
                # Create new device
                device = Device(
                    device_id=device_id,
                    location=location,
                    battery_level=battery_level,
                    empty_level=empty_level
                )
                self.devices[device_id] = device
                logger.info(f"Added new device: {device_id}")
                self.device_added.emit(device)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """
        Get a device by ID
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device instance or None if not found
        """
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[Device]:
        """
        Get all devices
        
        Returns:
            List of all Device instances
        """
        return list(self.devices.values())
    
    def get_device_count(self) -> int:
        """Get the number of tracked devices"""
        return len(self.devices)
    
    def remove_device(self, device_id: str) -> bool:
        """
        Remove a device from tracking
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if device was removed, False if not found
        """
        if device_id in self.devices:
            del self.devices[device_id]
            logger.info(f"Removed device: {device_id}")
            return True
        return False
    
    def clear_all(self):
        """Clear all devices"""
        self.devices.clear()
        logger.info("Cleared all devices")
    
    def _check_timeouts(self):
        """Check for devices that have timed out"""
        now = datetime.now()
        for device_id, device in list(self.devices.items()):
            if device.is_timed_out(DEVICE_TIMEOUT_SECONDS):
                if device.connected:  # Only emit signal if it was connected
                    device.mark_disconnected()
                    logger.info(f"Device {device_id} timed out (last update: {device.last_update})")
                    self.device_disconnected.emit(device)

