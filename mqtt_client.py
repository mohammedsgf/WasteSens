"""
MQTT Client for receiving device data from broker
"""
import json
import logging
from typing import Callable, Optional
import paho.mqtt.client as mqtt
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import config

logger = logging.getLogger(__name__)


class MQTTClient(QObject):
    """MQTT client that emits Qt signals when messages are received"""
    
    # Signal emitted when a device message is received
    # Arguments: topic (str), payload (dict)
    message_received = pyqtSignal(str, dict)
    
    # Signal emitted when connection status changes
    # Arguments: connected (bool), message (str)
    connection_changed = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = None
        self.connected = False
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self._attempt_reconnect)
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_delay = 5000  # 5 seconds
        self.subscribed = False
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            import uuid
            # Use unique client ID to avoid conflicts
            unique_client_id = f"{config.MQTT_CLIENT_ID}_{uuid.uuid4().hex[:8]}"
            self.client = mqtt.Client(client_id=unique_client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            
            # Set authentication if provided
            if config.MQTT_USERNAME and config.MQTT_PASSWORD:
                self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker at {config.MQTT_BROKER_HOST}:{config.MQTT_BROKER_PORT}")
            self.client.connect_async(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, config.MQTT_KEEPALIVE)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
            self.connection_changed.emit(False, f"Connection error: {str(e)}")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.reconnect_timer.stop()
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.connection_changed.emit(False, "Disconnected")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
            self.connection_changed.emit(True, "Connected")
            
            # Subscribe to topic pattern
            logger.info(f"Subscribing to topic: {config.MQTT_TOPIC_PATTERN}")
            result, mid = client.subscribe(config.MQTT_TOPIC_PATTERN)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Successfully subscribed to {config.MQTT_TOPIC_PATTERN} (mid: {mid})")
            else:
                logger.error(f"Failed to subscribe to {config.MQTT_TOPIC_PATTERN}, error code: {result}")
        else:
            self.connected = False
            error_msg = f"Connection failed with code {rc}"
            logger.error(error_msg)
            self.connection_changed.emit(False, error_msg)
            # Schedule reconnection attempt
            self.reconnect_timer.start(self.reconnect_delay)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection (rc={rc})")
            self.connection_changed.emit(False, "Unexpected disconnection")
            # Schedule reconnection attempt
            self.reconnect_timer.start(self.reconnect_delay)
        else:
            logger.info("Disconnected from MQTT broker")
            self.connection_changed.emit(False, "Disconnected")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscription is confirmed"""
        self.subscribed = True
        logger.info(f"Subscription confirmed (mid: {mid}, QoS: {granted_qos})")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            topic = msg.topic
            payload_str = msg.payload.decode('utf-8')
            logger.info(f"Received message on topic '{topic}': {payload_str}")
            
            # Parse JSON payload
            payload = json.loads(payload_str)
            logger.info(f"Parsed payload: {payload}")
            
            # Emit signal with parsed data
            self.message_received.emit(topic, payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message from topic '{msg.topic}': {e}")
            logger.error(f"Raw payload: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing message from topic '{msg.topic}': {e}")
    
    def _attempt_reconnect(self):
        """Attempt to reconnect to broker"""
        if not self.connected:
            logger.info("Attempting to reconnect to MQTT broker...")
            if self.client:
                try:
                    self.client.reconnect()
                except Exception as e:
                    logger.error(f"Reconnection failed: {e}")
                    self.reconnect_timer.start(self.reconnect_delay)
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected

