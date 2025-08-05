from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List


class HealthProfileCreate(BaseModel):
    user_id: UUID
    allergies: List[str] = []
    chronic_conditions: List[str] = []
    dietary_preferences: List[str] = []


class HealthProfileRead(BaseModel):
    id: UUID
    user_id: UUID
    allergies: List[str]
    chronic_conditions: List[str]
    dietary_preferences: List[str]
    updated_at: datetime

    class Config:
        orm_mode = True
