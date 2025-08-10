from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


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
        from_attributes = True


class AnalyzeRequest(BaseModel):
    title: str
    raw_text: str
    barcode: Optional[str] = None


class AnalyzeResponse(BaseModel):
    scan: ScanRead


class ScanListItem(BaseModel):
    id: UUID
    product_name: str
    created_at: datetime
