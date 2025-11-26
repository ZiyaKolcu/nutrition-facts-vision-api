from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ScanCreate(BaseModel):
    user_id: UUID
    product_name: str
    raw_text: str
    parsed_ingredients: List[str]
    summary_explanation: Optional[str] = None
    summary_risk: Optional[str] = None


class ScanRead(BaseModel):
    id: UUID
    user_id: UUID
    product_name: str
    raw_text: str
    parsed_ingredients: List[str]
    summary_explanation: Optional[str]
    summary_risk: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyzeRequest(BaseModel):
    title: str
    raw_text: str
    language: str 


class AnalyzeResponse(BaseModel):
    scan: ScanRead


class ScanListItem(BaseModel):
    id: UUID
    product_name: str
    created_at: datetime


class ScanDetailIngredient(BaseModel):
    name: str
    risk_level: str


class ScanDetailNutrient(BaseModel):
    label: str
    value: float


class ScanDetailResponse(BaseModel):
    id: UUID
    product_name: str
    summary_explanation: Optional[str]
    ingredients: List[ScanDetailIngredient]
    nutrients: List[ScanDetailNutrient]
