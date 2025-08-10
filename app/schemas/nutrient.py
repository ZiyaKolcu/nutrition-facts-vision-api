from pydantic import BaseModel
from uuid import UUID


class NutrientCreate(BaseModel):
    scan_id: UUID
    label: str
    value: float
    max_value: float


class NutrientRead(BaseModel):
    id: UUID
    scan_id: UUID
    label: str
    value: float
    max_value: float

    class Config:
        from_attributes = True
