"""Prompt builders for nutrition parsing, risk assessment, and unified analysis."""

from __future__ import annotations

from typing import List
import json


def _get_language_name(language_code: str) -> str:
    """Convert language code to language name for prompt instructions."""
    language_map = {
        "en": "English",
        "tr": "Turkish",
    }
    return language_map.get(language_code, "English")


def build_system_prompt_parse() -> str:
    return (
        "You are a nutrition label parsing assistant. Given raw OCR text from a food label, "
        "you will extract a cleaned ingredients list (as a single comma-separated string) and "
        "a structured JSON for nutrition per 100g and per portion when available. "
        "Return STRICT JSON with keys: ingredients_plain_text (string), nutrition (object)."
    )


def build_user_prompt_parse(raw_text: str) -> str:
    return (
        "Raw OCR text from label:\n" + raw_text + "\n\n"
        "Output format (STRICT JSON only, no extra text):\n"
        "{\n"
        '  "ingredients_plain_text": "Sugar, ...",\n'
        '  "nutrition": {\n'
        '    "energy": {"per_100g": number|null, "per_portion": number|null},\n'
        '    "fat": {"per_100g": number|null, "per_portion": number|null},\n'
        '    "saturated_fat": {"per_100g": number|null, "per_portion": number|null},\n'
        '    "trans_fat": {"per_100g": number|null, "per_portion": number|null},\n'
        '    "carbohydrate": {"per_100g": number|null, "per_portion": number|null},\n'
        '    "sugars": {"per_100g": number|null, "per_portion": number|null},\n'
        '    "dietary_fiber": {"per_100g": number|null, "per_portion": number|null},\n'
        '    "protein": {"per_100g": number|null, "per_portion": number|null},\n'
        '    "salt": {"per_100g": number|null, "per_portion": number|null}\n'
        "  }\n"
        "}"
    )


def build_system_prompt_unified(language: str = "en") -> str:
    """Build system prompt for unified analysis.

    Args:
        language: Language code ('en', 'tr', etc.). Affects the response language for
                 ingredients, nutrition labels, and summary_explanation. Risk levels ('Low', 'Medium', 'High') are always in English.
    """
    lang_name = _get_language_name(language)
    return (
        "You are a nutrition label analysis assistant. Given raw OCR text from a food label, "
        "you will: (1) extract a cleaned ingredients list as an array of strings, (2) extract a "
        "structured nutrition object for per_100g and per_portion when available, (3) classify "
        "each ingredient's risk as one of 'Low', 'Medium', or 'High' considering the user's health "
        "profile if provided (allergies, health conditions, dietary preferences), and (4) write a brief "
        "summary_explanation and an overall summary_risk as one of 'Low', 'Medium', or 'High'. "
        "If any ingredient matches a user allergy, its risk MUST be 'High'. Return STRICT JSON only with keys: "
        "ingredients (array), nutrition (object), risks (object), summary_explanation (string), summary_risk (string). "
        f"CRITICAL INSTRUCTION: ALL ingredient names, nutrition labels, and summary_explanation MUST be written ONLY in {lang_name}. "
        f"Do NOT use English. Do NOT mix languages. Every single ingredient name and nutrition label must be in {lang_name}. "
        f"Risk levels (Low, Medium, High) MUST always be in English."
    )


def build_user_prompt_unified(
    raw_text: str, profile_text: str, language: str = "en"
) -> str:
    return (
        profile_text
        + "Raw OCR text from label:\n"
        + raw_text
        + "\n\nOutput format (STRICT JSON only, no extra text):\n"
        + "{\n"
        + '  "ingredients": ["Sugar", "Salt", ...],\n'
        + '  "nutrition": {\n'
        + '    "energy": {"per_100g": number|null, "per_portion": number|null},\n'
        + '    "fat": {"per_100g": number|null, "per_portion": number|null},\n'
        + '    "saturated_fat": {"per_100g": number|null, "per_portion": number|null},\n'
        + '    "trans_fat": {"per_100g": number|null, "per_portion": number|null},\n'
        + '    "carbohydrate": {"per_100g": number|null, "per_portion": number|null},\n'
        + '    "sugars": {"per_100g": number|null, "per_portion": number|null},\n'
        + '    "dietary_fiber": {"per_100g": number|null, "per_portion": number|null},\n'
        + '    "protein": {"per_100g": number|null, "per_portion": number|null},\n'
        + '    "salt": {"per_100g": number|null, "per_portion": number|null}\n'
        + "  },\n"
        + '  "risks": {"Sugar": "Medium", "Peanuts": "High"},\n'
        + '  "summary_explanation": "Short explanation tailored to the profile.",\n'
        + '  "summary_risk": "Low"\n'
        + "}"
    )


def build_system_prompt_risk(language: str = "en") -> str:
    """Build system prompt for risk assessment.

    Args:
        language: Language code. Ingredient names in response will be in the specified language.
                 Risk levels are always in English.
    """
    lang_name = _get_language_name(language)
    return (
        "You are a nutrition safety assistant. Given a list of ingredient names, classify EACH "
        'ingredient\'s risk level as one of "Low", "Medium", or "High" strictly. Consider health '
        "profile if provided (allergies, health conditions, dietary preferences). If an ingredient "
        'matches any user allergy, it MUST be labeled "High". Return STRICT JSON mapping ingredient '
        "to risk label. "
        f"CRITICAL: Ingredient names in the response MUST be in {lang_name} ONLY. Do NOT use English. "
        f"Risk levels (Low, Medium, High) MUST always be in English. "
        'Example:\n{\n  "IngredientName": "Medium",\n  "AnotherIngredient": "High"\n}'
    )


def build_user_prompt_risk(ingredients: List[str], profile_text: str) -> str:
    return (
        profile_text
        + "Ingredients list (JSON array):\n"
        + json.dumps(ingredients, ensure_ascii=False)
    )
