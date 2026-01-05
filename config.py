"""
Configuration settings for the IoT Dashboard
"""
import os

# MQTT Broker Configuration
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'test.mosquitto.org')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))
MQTT_TOPIC_PATTERN = os.getenv('MQTT_TOPIC_PATTERN', 'smartwaste/+/data')
MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'smartwaste_dashboard')
MQTT_KEEPALIVE = 60

# MQTT Authentication (optional)
MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)

# Update Settings
UPDATE_INTERVAL_MS = 1000  # UI update interval in milliseconds

# Map Settings
DEFAULT_MAP_CENTER = (40.7128, -74.0060)  # Default: New York City
DEFAULT_ZOOM_LEVEL = 13

