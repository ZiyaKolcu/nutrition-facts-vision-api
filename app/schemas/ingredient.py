from pydantic import BaseModel
from uuid import UUID


class IngredientCreate(BaseModel):
    scan_id: UUID
    name: str
    risk_level: str


class IngredientRead(BaseModel):
    id: UUID
    scan_id: UUID
    name: str
    risk_level: str

    class Config:
        from_attributes = True
