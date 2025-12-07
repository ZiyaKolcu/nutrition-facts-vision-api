from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.scan import Scan
from app.models.ingredient import Ingredient
from app.models.nutrient import Nutrient
from app.schemas.scan import (
    ScanRead,
    AnalyzeRequest,
    AnalyzeResponse,
    ScanListItem,
    ScanDetailResponse,
    ScanDetailIngredient,
    ScanDetailNutrient,
)
from app.services.nutrition.nutrition_analyzer import analyze_label_for_user
from app.services.nutrition.label_parser import parse_ocr_raw_text
from app.services.nutrition.health_risk_assessor import assess_ingredient_risks
from app.services.health_profile import health_profile as hp_service


router = APIRouter()


@router.post(
    "/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_201_CREATED
)
def analyze_label(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Initialize variables with safe defaults
    ingredients_list = []
    nutrition_map = {}
    risk_map = {}
    summary_explanation = None
    summary_risk = None

    try:
        result = analyze_label_for_user(
            db, current_user.id, body.raw_text, language=body.language
        )
        # Safely unpack the result
        if isinstance(result, tuple) and len(result) == 5:
            (
                ingredients_list,
                nutrition_map,
                risk_map,
                summary_explanation,
                summary_risk,
            ) = result

            # Validate and fix ingredients_list immediately
            if not isinstance(ingredients_list, list):
                if isinstance(ingredients_list, str):
                    ingredients_list = [
                        token.strip()
                        for token in ingredients_list.split(",")
                        if token.strip()
                    ]
                else:
                    ingredients_list = []
        else:
            raise ValueError(
                f"Unexpected result format from analyze_label_for_user: {type(result)}, length: {len(result) if isinstance(result, (tuple, list)) else 'N/A'}"
            )
    except ValueError as e:
        try:
            ingredients_list, nutrition_map = parse_ocr_raw_text(body.raw_text)

            # Validate and fix ingredients_list immediately
            if not isinstance(ingredients_list, list):
                if isinstance(ingredients_list, str):
                    ingredients_list = [
                        token.strip()
                        for token in ingredients_list.split(",")
                        if token.strip()
                    ]
                else:
                    ingredients_list = []

        except ValueError as parsing_error:
            raise HTTPException(
                status_code=502, detail=f"Parsing failed: {parsing_error}"
            ) from parsing_error
        except Exception as unexpected_error:
            raise HTTPException(
                status_code=500, detail=f"Unexpected parsing error: {unexpected_error}"
            ) from unexpected_error

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
                ingredients_list, health_profile=profile_dict, language=body.language
            )
        except ValueError:
            risk_map = {name: "Low" for name in ingredients_list}
        except Exception as risk_error:
            # Fallback to Low risk for all ingredients
            risk_map = {name: "Low" for name in ingredients_list}

        summary_explanation = None
        summary_risk = None
    except Exception as unexpected_error:
        raise HTTPException(
            status_code=500, detail=f"Unexpected analysis error: {unexpected_error}"
        ) from unexpected_error

    # Validate and fix data structures
    if not isinstance(ingredients_list, list):
        # Try to convert to list if it's a string
        if isinstance(ingredients_list, str):
            ingredients_list = [
                token.strip() for token in ingredients_list.split(",") if token.strip()
            ]
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid ingredients_list type: expected list, got {type(ingredients_list).__name__}",
            )

    if not isinstance(nutrition_map, dict):
        raise HTTPException(
            status_code=500,
            detail=f"Invalid nutrition_map type: expected dict, got {type(nutrition_map).__name__}. Value: {str(nutrition_map)[:200]}",
        )

    if not isinstance(risk_map, dict):
        raise HTTPException(
            status_code=500,
            detail=f"Invalid risk_map type: expected dict, got {type(risk_map).__name__}. Value: {str(risk_map)[:200]}",
        )

    scan = Scan(
        user_id=current_user.id,
        product_name=body.title,
        raw_text=body.raw_text,
        parsed_ingredients=ingredients_list,
        summary_explanation=summary_explanation,
        summary_risk=summary_risk,
    )
    db.add(scan)
    db.flush()

    for name in ingredients_list:
        db.add(Ingredient(scan_id=scan.id, name=name, risk_level=risk_map.get(name)))

    # Extract nutrition values from the normalized structure
    # Handle case where nutrition_map might not be a dict
    if isinstance(nutrition_map, dict):
        nutrition_values = nutrition_map.get("values", {})
        if isinstance(nutrition_values, dict):
            for label, value in nutrition_values.items():
                # Skip None values and the 'micros' dict
                if value is None or label == "micros":
                    continue
                # Handle micros separately if needed
                if isinstance(value, dict):
                    continue
                db.add(
                    Nutrient(
                        scan_id=scan.id,
                        label=label,
                        value=value,
                        max_value=None,
                    )
                )

    db.commit()
    db.refresh(scan)

    return AnalyzeResponse(scan=ScanRead.model_validate(scan))


@router.get("/me", response_model=List[ScanListItem])
def get_all_scans_by_user_id(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scans = (
        db.query(Scan.id, Scan.product_name, Scan.created_at)
        .filter(Scan.user_id == current_user.id)
        .order_by(Scan.created_at.desc())
        .all()
    )
    return [
        {"id": scan_id, "product_name": product_name, "created_at": created_at}
        for scan_id, product_name, created_at in scans
    ]


@router.get("/{scan_id}", response_model=ScanDetailResponse)
def get_scan_by_scan_id(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve detailed scan information for a given scan_id, including:
    - summary_explanation from scans table
    - all ingredients (name, risk_level) for this scan
    - all nutrients (label, value) for this scan
    Only allows access to scans belonging to the current user.
    """
    scan = (
        db.query(Scan)
        .filter(Scan.id == scan_id, Scan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Fetch ingredients for this scan
    ingredients = db.query(Ingredient).filter(Ingredient.scan_id == scan_id).all()
    ingredient_list = [
        ScanDetailIngredient(name=ing.name, risk_level=ing.risk_level)
        for ing in ingredients
    ]

    # Fetch nutrients for this scan
    nutrients = db.query(Nutrient).filter(Nutrient.scan_id == scan_id).all()
    nutrient_list = [
        ScanDetailNutrient(label=nut.label, value=float(nut.value)) for nut in nutrients
    ]

    return ScanDetailResponse(
        id=scan.id,
        product_name=scan.product_name,
        summary_explanation=scan.summary_explanation,
        ingredients=ingredient_list,
        nutrients=nutrient_list,
    )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan_by_scan_id(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = (
        db.query(Scan)
        .filter(Scan.id == scan_id, Scan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    db.delete(scan)
    db.commit()
    return None
