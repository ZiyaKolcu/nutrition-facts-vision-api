from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional


class HealthProfileCreate(BaseModel):
    user_id: UUID
    allergies: List[str] = []
    health_conditions: List[str] = []
    dietary_preferences: List[str] = []
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None


class HealthProfileRead(BaseModel):
    id: UUID
    user_id: UUID
    allergies: List[str]
    health_conditions: List[str]
    dietary_preferences: List[str]
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthProfileUpdate(BaseModel):
    allergies: Optional[List[str]] = None
    health_conditions: Optional[List[str]] = None
    dietary_preferences: Optional[List[str]] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
