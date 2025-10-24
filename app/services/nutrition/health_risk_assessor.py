"""Ingredient risk assessment utilities."""

from __future__ import annotations

import re
import unicodedata
import json
from typing import Any, Dict, List, Optional
from app.services.nutrition.openai_client import call_openai_json
from app.services.nutrition.prompt_templates import (
    build_system_prompt_risk,
    build_user_prompt_risk,
)


def _normalize_token(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text_norm = unicodedata.normalize("NFKD", text)
    text_ascii = text_norm.encode("ascii", "ignore").decode("ascii")
    text_ascii = text_ascii.lower()
    text_ascii = re.sub(r"[^a-z0-9]+", " ", text_ascii).strip()
    return text_ascii


def _is_allergen_match(ingredient_name: str, allergy_terms: List[str]) -> bool:
    ing = _normalize_token(ingredient_name)
    if not ing:
        return False
    ing_tokens = set(ing.split())
    for term in allergy_terms or []:
        norm = _normalize_token(term)
        if not norm:
            continue
        norm_tokens = set(norm.split())
        if ing_tokens & norm_tokens:
            return True
        if norm in ing or ing in norm:
            return True
    return False


def assess_ingredient_risks(
    ingredients: List[str], health_profile: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """Classify each ingredient risk level as one of: "Low", "Medium", "High".

    Deterministic override: if an ingredient matches any user allergy, label "High".
    """
    profile_text = ""
    if health_profile:
        allergies = health_profile.get("allergies") or []
        health_conditions = health_profile.get("health_conditions") or []
        prefs = health_profile.get("dietary_preferences") or []
        profile_text = (
            "User health profile:\n"
            f"Allergies: {', '.join(allergies) if allergies else 'None'}\n"
            f"Health conditions: {', '.join(health_conditions) if health_conditions else 'None'}\n"
            f"Dietary preferences: {', '.join(prefs) if prefs else 'None'}\n\n"
        )

    system_prompt = build_system_prompt_risk()
    user_prompt = build_user_prompt_risk(ingredients, profile_text)

    data = call_openai_json(system_prompt, user_prompt)
    risks: Dict[str, str] = {}
    if isinstance(data, dict):
        for name, label in data.items():
            if not isinstance(name, str):
                continue
            if isinstance(label, str) and label in {"Low", "Medium", "High"}:
                risks[name.strip()] = label

    allergy_list: List[str] = []
    if health_profile and isinstance(health_profile.get("allergies"), list):
        allergy_list = health_profile.get("allergies")

    if allergy_list:
        for ing in ingredients:
            if _is_allergen_match(ing, allergy_list):
                risks[ing] = "High"

    for ing in ingredients:
        risks.setdefault(ing, "Low")

    return risks


def json_dumps_safe(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)
