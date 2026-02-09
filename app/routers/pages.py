"""
Page routes: landing page, sign in, sign up.
Serves Jinja2 templates.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def landing_page(request: Request):
    """Landing / marketing page."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/signin")
async def signin_page(request: Request):
    """Sign in page. Redirects to dashboard if already authenticated."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        user = get_current_user(request, db)
        if user:
            return RedirectResponse(url="/dashboard", status_code=302)
    finally:
        db.close()
    return templates.TemplateResponse("signin.html", {"request": request})


@router.get("/signup")
async def signup_page(request: Request):
    """Sign up page. Redirects to dashboard if already authenticated."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        user = get_current_user(request, db)
        if user:
            return RedirectResponse(url="/dashboard", status_code=302)
    finally:
        db.close()
    return templates.TemplateResponse("signup.html", {"request": request})
