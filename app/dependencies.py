"""
FastAPI dependencies for database sessions and authentication.
"""
from typing import Generator, Optional
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.services.auth import decode_access_token

# Cookie name for JWT token
ACCESS_TOKEN_COOKIE = "access_token"


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Automatically closes the session when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency that extracts and validates the JWT from an HttpOnly cookie.
    Returns the User object or None if not authenticated.
    """
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user


def require_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    """
    Dependency that requires authentication.
    Raises 401 if the user is not authenticated.
    """
    user = get_current_user(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user
