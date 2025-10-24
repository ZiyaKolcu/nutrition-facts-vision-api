from sqlalchemy.orm import Session
from app.models.health_profile import HealthProfile
from app.schemas.health_profile import HealthProfileCreate, HealthProfileUpdate
from sqlalchemy.exc import NoResultFound


def get_health_profile_by_user(db: Session, user_id):
    return db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()


def create_health_profile(db: Session, profile_in: HealthProfileCreate):
    db_profile = HealthProfile(
        user_id=profile_in.user_id,
        allergies=profile_in.allergies,
        health_conditions=profile_in.health_conditions,
        dietary_preferences=profile_in.dietary_preferences,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_health_profile(
    db: Session, db_profile: HealthProfile, profile_in: HealthProfileUpdate
):
    update_data = profile_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    db.commit()
    db.refresh(db_profile)
    return db_profile
