"""
FastAPI application factory with lifespan management.
"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import create_tables
from app.services.mqtt import MQTTService
from app.services.device_manager import device_manager
from app.routers import pages, auth, dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# MQTT service instance (module-level so it persists)
mqtt_service = MQTTService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: runs on startup and shutdown.
    - Creates database tables
    - Starts MQTT client
    - Starts device timeout checker
    """
    # --- Startup ---
    logger.info("Starting Smart Waste IoT Dashboard (web)...")

    # Create database tables
    create_tables()
    logger.info("Database tables created / verified.")

    # Give the device manager access to the running event loop
    loop = asyncio.get_running_loop()
    device_manager.set_event_loop(loop)

    # Wire MQTT -> DeviceManager
    mqtt_service.set_message_callback(device_manager.process_mqtt_message)
    mqtt_service.connect()

    # Start background timeout checker
    timeout_task = asyncio.create_task(device_manager.start_timeout_checker())

    logger.info("Application started.")

    yield  # Application is running

    # --- Shutdown ---
    logger.info("Shutting down...")
    timeout_task.cancel()
    mqtt_service.disconnect()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include routers
    app.include_router(pages.router)
    app.include_router(auth.router)
    app.include_router(dashboard.router)

    return app


app = create_app()
