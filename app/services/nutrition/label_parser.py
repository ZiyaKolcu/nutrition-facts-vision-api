"""Parsing helpers for OCR text and nutrition normalization."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from app.services.nutrition.openai_client import call_openai_json
from app.services.nutrition.prompt_templates import (
    build_system_prompt_parse,
    build_user_prompt_parse,
)


EXPECTED_NUTRITION_KEYS = [
    "energy",
    "fat",
    "saturated_fat",
    "trans_fat",
    "carbohydrate",
    "sugars",
    "dietary_fiber",
    "protein",
    "salt",
]


def _to_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[-+]?[0-9]+(?:[\.,][0-9]+)?", value)
        if match:
            try:
                return float(match.group(0).replace(",", "."))
            except (ValueError, TypeError):
                return None
    return None


def normalize_nutrition(
    nutrition: Dict[str, Any],
) -> Dict[str, Dict[str, Optional[float]]]:
    if not isinstance(nutrition, dict):
        return {}
    normalized: Dict[str, Dict[str, Optional[float]]] = {}
    for key in EXPECTED_NUTRITION_KEYS:
        entry = nutrition.get(key)
        if isinstance(entry, dict):
            per_100g = _to_number(entry.get("per_100g"))
            per_portion = _to_number(entry.get("per_portion"))
            normalized[key] = {
                "per_100g": per_100g if per_100g is not None else None,
                "per_portion": per_portion if per_portion is not None else None,
            }
    return normalized


def parse_ocr_raw_text(
    raw_text: str,
) -> Tuple[List[str], Dict[str, Dict[str, Optional[float]]]]:
    """
    Parse OCR raw text and return (ingredients_list, nutrition_map).

    nutrition_map structure:
      { label: {"per_100g": float|None, "per_portion": float|None }, ... }
    """
    system_prompt = build_system_prompt_parse()
    user_prompt = build_user_prompt_parse(raw_text)
    data = call_openai_json(system_prompt, user_prompt)

    ingredients_plain = str(data.get("ingredients_plain_text", "")).strip()
    ingredients_list = [
        token.strip()
        for token in ingredients_plain.split(",")
        if token and token.strip()
    ]

    nutrition = data.get("nutrition") or {}
    normalized = normalize_nutrition(nutrition)

    return ingredients_list, normalized
