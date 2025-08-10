from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.scan import Scan
from app.models.ingredient import Ingredient
from app.models.nutrient import Nutrient
from app.schemas.scan import ScanRead
from app.services.nutrition.nutrition_analyzer import analyze_label_for_user
from app.services.nutrition.label_parser import parse_ocr_raw_text
from app.services.nutrition.health_risk_assessor import assess_ingredient_risks
from app.services.health_profile import health_profile as hp_service


router = APIRouter()


class AnalyzeRequest(BaseModel):
    title: str
    raw_text: str
    barcode: Optional[str] = None


class AnalyzeResponse(BaseModel):
    scan: ScanRead


@router.post(
    "/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_201_CREATED
)
def analyze_label(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        (
            ingredients_list,
            nutrition_map,
            risk_map,
            summary_explanation,
            summary_risk,
        ) = analyze_label_for_user(db, current_user.id, body.raw_text)
    except ValueError:
        try:
            ingredients_list, nutrition_map = parse_ocr_raw_text(body.raw_text)
        except ValueError as parsing_error:
            raise HTTPException(
                status_code=502, detail=f"Parsing failed: {parsing_error}"
            ) from parsing_error
        profile = hp_service.get_health_profile_by_user(db, current_user.id)
        profile_dict = None
        if profile:
            profile_dict = {
                "allergies": profile.allergies or [],
                "chronic_conditions": profile.chronic_conditions or [],
                "dietary_preferences": profile.dietary_preferences or [],
            }
        try:
            risk_map = assess_ingredient_risks(
                ingredients_list, health_profile=profile_dict
            )
        except ValueError:
            risk_map = {name: "Low" for name in ingredients_list}
        summary_explanation = None
        summary_risk = None

    scan = Scan(
        user_id=current_user.id,
        product_name=body.title,
        barcode=body.barcode,
        raw_text=body.raw_text,
        parsed_ingredients=ingredients_list,
        summary_explanation=summary_explanation,
        summary_risk=summary_risk,
    )
    db.add(scan)
    db.flush()  

    for name in ingredients_list:
        db.add(Ingredient(scan_id=scan.id, name=name, risk_level=risk_map.get(name)))

    for label, values in nutrition_map.items():
        per_100g = values.get("per_100g")
        per_portion = values.get("per_portion")
        if per_100g is not None:
            db.add(
                Nutrient(
                    scan_id=scan.id,
                    label=f"{label}_per_100g",
                    value=per_100g,
                    max_value=None,
                )
            )
        if per_portion is not None:
            db.add(
                Nutrient(
                    scan_id=scan.id,
                    label=f"{label}_per_portion",
                    value=per_portion,
                    max_value=None,
                )
            )

    db.commit()
    db.refresh(scan)

    return AnalyzeResponse(scan=ScanRead.from_orm(scan))
