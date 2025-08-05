from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    firebase_uid: str
    email: EmailStr


class UserRead(BaseModel):
    id: UUID
    firebase_uid: str
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True
