"""Authentication API endpoints for Firebase token verification."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserRead
from app.services.auth.user_auth import authenticate_user

router = APIRouter()


class AuthRequest(BaseModel):
    """Request model for authentication endpoint."""

    id_token: str


class AuthResponse(BaseModel):
    """Response model for authentication endpoint."""

    user: UserRead
    message: str


@router.post("/authenticate", response_model=AuthResponse)
async def authenticate_user_endpoint(
    auth_request: AuthRequest, db: Session = Depends(get_db)
):
    """
    Authenticates a user using Firebase ID token.
    If user doesn't exist in database, creates a new user record.

    Args:
        auth_request (AuthRequest): Contains the Firebase ID token
        db (Session): Database session

    Returns:
        AuthResponse: User information and authentication status
    """
    try:
        user = authenticate_user(db, auth_request.id_token)

        return AuthResponse(
            user=UserRead.from_orm(user), message="Authentication successful"
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc


@router.get("/me", response_model=UserRead)
async def get_current_user_endpoint(current_user: User = Depends(get_current_user)):
    """
    Gets the current authenticated user information.

    Args:
        current_user (User): Current authenticated user from dependency

    Returns:
        UserRead: Current user information
    """
    return UserRead.from_orm(current_user)
