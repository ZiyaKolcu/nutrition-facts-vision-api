from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class ScanCreate(BaseModel):
    user_id: UUID
    product_name: str
    barcode: Optional[str] = None
    raw_text: str
    parsed_ingredients: List[str]
    summary_explanation: Optional[str] = None
    summary_risk: Optional[str] = None


class ScanRead(BaseModel):
    id: UUID
    user_id: UUID
    product_name: str
    barcode: Optional[str]
    raw_text: str
    parsed_ingredients: List[str]
    summary_explanation: Optional[str]
    summary_risk: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
