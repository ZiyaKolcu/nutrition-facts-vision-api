"""API dependencies for database and authentication."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.user_auth import authenticate_user
from app.models.user import User


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(id_token: str, db: Session = Depends(get_db)) -> User:
    """
    Dependency to get the current authenticated user.
    Can be used in other routes that require authentication.

    Args:
        id_token (str): Firebase ID token from request
        db (Session): Database session

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: If authentication fails
    """
    try:
        user = authenticate_user(db, id_token)
        return user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        ) from exc
