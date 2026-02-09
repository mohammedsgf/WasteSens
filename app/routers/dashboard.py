"""
Dashboard routes: protected page, device REST API, WebSocket endpoint.
All device data is scoped to the authenticated user.
"""
import logging
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_db, ACCESS_TOKEN_COOKIE
from app.services.auth import decode_access_token
from app.services.device_manager import device_manager
from app.config import settings
from app.database import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


def _get_user_from_cookie(request_or_websocket) -> int | None:
    """Extract user_id from the JWT cookie. Returns user_id or None."""
    token = request_or_websocket.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        return int(sub)
    except (ValueError, TypeError):
        return None


@router.get("/dashboard")
async def dashboard_page(request: Request):
    """
    Dashboard page (protected).
    Redirects to /signin if no valid JWT cookie.
    """
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
                "user_id": user.id,
                "map_center_lat": settings.DEFAULT_MAP_CENTER_LAT,
                "map_center_lng": settings.DEFAULT_MAP_CENTER_LNG,
                "map_zoom": settings.DEFAULT_ZOOM_LEVEL,
            },
        )
    finally:
        db.close()


@router.get("/api/devices")
async def get_all_devices(request: Request):
    """Return all devices belonging to the authenticated user."""
    db = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        devices = device_manager.get_devices_for_user(user.id)
        return [d.to_dict() for d in devices]
    finally:
        db.close()


@router.get("/api/devices/{device_id}")
async def get_device(device_id: str, request: Request):
    """Return a single device by ID, scoped to the authenticated user."""
    db = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        device = device_manager.get_device(user.id, device_id)
        if device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )
        return device.to_dict()
    finally:
        db.close()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time device updates.
    Authenticates via JWT cookie before accepting.
    Only sends events for devices belonging to the authenticated user.
    """
    # Authenticate BEFORE accepting the WebSocket
    user_id = _get_user_from_cookie(websocket)
    if user_id is None:
        await websocket.close(code=4001, reason="Not authenticated")
        return

    await device_manager.ws_manager.connect(websocket, user_id)
    try:
        # Send current device state for this user on connect
        devices = device_manager.get_devices_for_user(user_id)
        for device in devices:
            await websocket.send_json(
                {"event": "device_added", "device": device.to_dict()}
            )

        # Keep connection alive, listen for client messages (e.g., pings)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        device_manager.ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        device_manager.ws_manager.disconnect(websocket, user_id)
