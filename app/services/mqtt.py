"""
MQTT Client service for receiving device data from broker.
Plain Python implementation (no PyQt5 dependencies).
"""
import json
import uuid
import logging
import threading
from typing import Callable, Optional
import paho.mqtt.client as mqtt
from app.config import settings

logger = logging.getLogger(__name__)


class MQTTService:
    """MQTT client that calls a callback when messages are received."""

    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected: bool = False
        self.on_message_callback: Optional[Callable] = None
        self.on_connection_change_callback: Optional[Callable] = None
        self._lock = threading.Lock()

    def set_message_callback(self, callback: Callable[[str, dict], None]):
        """
        Set callback for incoming MQTT messages.

        Args:
            callback: Function(topic: str, payload: dict)
        """
        self.on_message_callback = callback

    def set_connection_callback(self, callback: Callable[[bool, str], None]):
        """
        Set callback for connection status changes.

        Args:
            callback: Function(connected: bool, message: str)
        """
        self.on_connection_change_callback = callback

    def connect(self):
        """Connect to the MQTT broker and start the network loop."""
        try:
            unique_id = f"{settings.MQTT_CLIENT_ID}_{uuid.uuid4().hex[:8]}"
            self.client = mqtt.Client(client_id=unique_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe

            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

            logger.info(
                f"Connecting to MQTT broker at "
                f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}"
            )
            self.client.connect_async(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                settings.MQTT_KEEPALIVE,
            )
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
            if self.on_connection_change_callback:
                self.on_connection_change_callback(False, f"Connection error: {e}")

    def disconnect(self):
        """Disconnect from the MQTT broker and stop the network loop."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT client disconnected")
            if self.on_connection_change_callback:
                self.on_connection_change_callback(False, "Disconnected")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
            if self.on_connection_change_callback:
                self.on_connection_change_callback(True, "Connected")

            topic = settings.MQTT_TOPIC_PATTERN
            logger.info(f"Subscribing to topic: {topic}")
            result, mid = client.subscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to {topic} (mid: {mid})")
            else:
                logger.error(f"Failed to subscribe, error code: {result}")
        else:
            self.connected = False
            msg = f"Connection failed with code {rc}"
            logger.error(msg)
            if self.on_connection_change_callback:
                self.on_connection_change_callback(False, msg)

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (rc={rc})")
            if self.on_connection_change_callback:
                self.on_connection_change_callback(False, "Unexpected disconnection")
        else:
            logger.info("Disconnected from MQTT broker")
            if self.on_connection_change_callback:
                self.on_connection_change_callback(False, "Disconnected")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscription is confirmed."""
        logger.info(f"Subscription confirmed (mid: {mid}, QoS: {granted_qos})")

    def _on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        try:
            topic = msg.topic
            payload_str = msg.payload.decode("utf-8")
            logger.info(f"Received message on '{topic}': {payload_str}")

            payload = json.loads(payload_str)

            if self.on_message_callback:
                self.on_message_callback(topic, payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from '{msg.topic}': {e}")
        except Exception as e:
            logger.error(f"Error processing message from '{msg.topic}': {e}")

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.connected
