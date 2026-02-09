"""
Application configuration using pydantic-settings.
Loads from environment variables and .env file.
"""
import os
import secrets
import logging
from pydantic_settings import BaseSettings
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = "change-this-to-a-random-secret-key-in-production"


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file"""

    # Application
    APP_NAME: str = "Smart Waste IoT Dashboard"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./data/smartwaste.db"

    # JWT Authentication
    SECRET_KEY: str = _DEFAULT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # MQTT Broker
    MQTT_BROKER_HOST: str = "test.mosquitto.org"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC_PATTERN: str = "smartwaste/+/+/data"
    MQTT_CLIENT_ID: str = "smartwaste_dashboard"
    MQTT_KEEPALIVE: int = 60
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None

    # Map defaults
    DEFAULT_MAP_CENTER_LAT: float = 40.7128
    DEFAULT_MAP_CENTER_LNG: float = -74.0060
    DEFAULT_ZOOM_LEVEL: int = 13

    # Device timeout (seconds)
    DEVICE_TIMEOUT_SECONDS: int = 10

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton settings instance
settings = Settings()

# Warn if using the default placeholder secret key
if settings.SECRET_KEY == _DEFAULT_SECRET:
    _generated = secrets.token_hex(32)
    settings.SECRET_KEY = _generated
    logger.warning(
        "SECRET_KEY is using the default placeholder. "
        "A random key has been generated for this session. "
        "Set a permanent SECRET_KEY in your .env file for production."
    )
