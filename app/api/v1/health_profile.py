from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.health_profile import (
    HealthProfileCreate,
    HealthProfileRead,
    HealthProfileUpdate,
)
from app.services import health_profile as hp_service

router = APIRouter()


@router.get("/me", response_model=HealthProfileRead)
def read_my_health_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = hp_service.get_health_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    return profile


@router.post(
    "/me", response_model=HealthProfileRead, status_code=status.HTTP_201_CREATED
)
def create_my_health_profile(
    profile_in: HealthProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = hp_service.get_health_profile_by_user(db, current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Health profile already exists")
    # Ensure user_id matches current user
    if profile_in.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Cannot create profile for another user"
        )
    return hp_service.create_health_profile(db, profile_in)


@router.put("/me", response_model=HealthProfileRead)
def update_my_health_profile(
    profile_in: HealthProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_profile = hp_service.get_health_profile_by_user(db, current_user.id)
    if not db_profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    return hp_service.update_health_profile(db, db_profile, profile_in)
