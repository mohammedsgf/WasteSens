"""
Dashboard routes: protected page, device REST API, WebSocket endpoint.
"""
import logging
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_db
from app.services.device_manager import device_manager
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard")
async def dashboard_page(request: Request):
    """
    Dashboard page (protected).
    Redirects to /signin if no valid JWT cookie.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse(url="/signin", status_code=302)
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user_name": user.name,
                "map_center_lat": settings.DEFAULT_MAP_CENTER_LAT,
                "map_center_lng": settings.DEFAULT_MAP_CENTER_LNG,
                "map_zoom": settings.DEFAULT_ZOOM_LEVEL,
            },
        )
    finally:
        db.close()


@router.get("/api/devices")
async def get_all_devices():
    """Return all currently tracked devices as JSON."""
    devices = device_manager.get_all_devices()
    return [d.to_dict() for d in devices]


@router.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Return a single device by ID."""
    device = device_manager.get_device(device_id)
    if device is None:
        return {"error": "Device not found"}, 404
    return device.to_dict()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time device updates.
    Clients receive JSON messages: {event, device}.
    """
    await device_manager.ws_manager.connect(websocket)
    try:
        # Send current device state on connect
        devices = device_manager.get_all_devices()
        for device in devices:
            await websocket.send_json(
                {"event": "device_added", "device": device.to_dict()}
            )

        # Keep connection alive, listen for client messages (e.g., pings)
        while True:
            data = await websocket.receive_text()
            # Client can send "ping" to keep alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        device_manager.ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        device_manager.ws_manager.disconnect(websocket)
