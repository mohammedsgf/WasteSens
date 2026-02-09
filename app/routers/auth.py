"""
Authentication API routes: sign up, sign in, sign out.
Uses HttpOnly cookies for JWT storage.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, ACCESS_TOKEN_COOKIE
from app.models.user import User
from app.schemas.user import SignUpRequest, SignInRequest
from app.services.auth import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup")
async def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Returns 201 on success, 400 if email already exists or passwords don't match.
    """
    # Validate passwords match
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    # Check if email already exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Create user
    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered: {user.email}")
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Account created successfully. Please sign in."},
    )


@router.post("/signin")
async def signin(data: SignInRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and set a JWT cookie.

    Returns 200 with a Set-Cookie header on success, 401 on invalid credentials.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Create JWT token with user id as subject
    token = create_access_token(data={"sub": str(user.id), "name": user.name})

    response = JSONResponse(
        content={"message": "Signed in successfully.", "name": user.name}
    )
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,  # 24 hours
        path="/",
    )

    logger.info(f"User signed in: {user.email}")
    return response


@router.post("/signout")
async def signout():
    """
    Sign out the current user by clearing the JWT cookie.
    """
    response = JSONResponse(content={"message": "Signed out successfully."})
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/")
    return response
