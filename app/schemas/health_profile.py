from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List


class HealthProfileCreate(BaseModel):
    user_id: UUID
    allergies: List[str] = []
    health_conditions: List[str] = []
    dietary_preferences: List[str] = []


class HealthProfileRead(BaseModel):
    id: UUID
    user_id: UUID
    allergies: List[str]
    health_conditions: List[str]
    dietary_preferences: List[str]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthProfileUpdate(BaseModel):
    allergies: List[str] = None
    health_conditions: List[str] = None
    dietary_preferences: List[str] = None
    age: int = None
    gender: str = None
    height_cm: int = None
    weight_kg: int = None
