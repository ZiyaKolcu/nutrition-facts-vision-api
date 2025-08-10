"""Unified label analysis orchestrating parsing, risk assessment, and summary."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.health_profile import health_profile as hp_service
from app.services.nutrition.openai_client import call_openai_json
from app.services.nutrition.prompt_templates import (
    build_system_prompt_unified,
    build_user_prompt_unified,
)
from app.services.nutrition.label_parser import normalize_nutrition
from app.services.nutrition.health_risk_assessor import _is_allergen_match


def _profile_to_text(profile: Optional[Dict[str, Any]]) -> str:
    if not profile:
        return ""
    allergies = profile.get("allergies") or []
    chronic = profile.get("chronic_conditions") or []
    prefs = profile.get("dietary_preferences") or []
    return (
        "User health profile:\n"
        f"Allergies: {', '.join(allergies) if allergies else 'None'}\n"
        f"Chronic conditions: {', '.join(chronic) if chronic else 'None'}\n"
        f"Dietary preferences: {', '.join(prefs) if prefs else 'None'}\n\n"
    )


def analyze_label_with_profile(
    raw_text: str, health_profile: Optional[Dict[str, Any]]
) -> Tuple[
    List[str],
    Dict[str, Dict[str, Optional[float]]],
    Dict[str, str],
    str,
    str,
]:
    """Single-call analysis that returns ingredients, normalized nutrition map,
    ingredient risk labels, a short explanation, and an overall risk.
    """
    system_prompt = build_system_prompt_unified()
    user_prompt = build_user_prompt_unified(raw_text, _profile_to_text(health_profile))
    data = call_openai_json(system_prompt, user_prompt)

    ingredients_list: List[str] = []
    if isinstance(data.get("ingredients"), list):
        ingredients_list = [
            str(token).strip()
            for token in data["ingredients"]
            if isinstance(token, (str, int, float)) and str(token).strip()
        ]

    nutrition = data.get("nutrition") or {}
    normalized = normalize_nutrition(nutrition)

    risks: Dict[str, str] = {}
    if isinstance(data.get("risks"), dict):
        for name, label in data["risks"].items():
            if (
                isinstance(name, str)
                and isinstance(label, str)
                and label in {"Low", "Medium", "High"}
            ):
                risks[name.strip()] = label

    allergy_list: List[str] = []
    if health_profile and isinstance(health_profile.get("allergies"), list):
        allergy_list = health_profile.get("allergies")
    if allergy_list:
        for ing in ingredients_list:
            if _is_allergen_match(ing, allergy_list):
                risks[ing] = "High"
    for ing in ingredients_list:
        risks.setdefault(ing, "Low")

    summary_explanation = str(data.get("summary_explanation") or "").strip()
    summary_risk = str(data.get("summary_risk") or "").strip()
    if summary_risk not in {"Low", "Medium", "High"}:
        summary_risk = "Low"

    return ingredients_list, normalized, risks, summary_explanation, summary_risk



def analyze_label_for_user(db: "Session", user_id: "UUID", raw_text: str) -> Tuple[
    List[str],
    Dict[str, Dict[str, Optional[float]]],
    Dict[str, str],
    str,
    str,
]:
    profile = hp_service.get_health_profile_by_user(db, user_id)
    profile_dict: Optional[Dict[str, Any]] = None
    if profile:
        profile_dict = {
            "allergies": profile.allergies or [],
            "chronic_conditions": profile.chronic_conditions or [],
            "dietary_preferences": profile.dietary_preferences or [],
        }
    return analyze_label_with_profile(raw_text, profile_dict)

