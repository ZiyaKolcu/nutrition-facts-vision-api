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
    return language_map.get(language_code.lower(), "English")


def build_system_prompt_parse() -> str:
    return (
        "You are a nutrition label parsing assistant. Your input is raw, unstructured OCR text "
        "which may contain mixed data for both '100g' and 'Per Portion'.\n\n"
        "*** CRITICAL EXTRACTION RULES ***\n"
        "1. IDENTIFY CONTEXT: Scan the text for keywords like '100g', '100ml' vs 'Porsiyon', 'Serving', 'Paket'.\n"
        "2. THE PRIORITY RULE (100g/ml OVERRIDES EVERYTHING):\n"
        "   - IF the text contains values associated with '100g' or '100ml', YOU MUST EXTRACT THOSE VALUES ONLY.\n"
        "   - IGNORE any numbers associated with 'Per Portion', '1 Paket', 'Serving' if 100g data is present.\n"
        "   - ONLY if '100g/ml' is completely missing, then extract the 'Per Portion' values.\n"
        "3. NO COLUMNS ASSUMPTION: The text is flat. Associate numbers with the nearest nutrient label based on proximity.\n"
        "4. MICROS: Look for vitamins/minerals (e.g. Calcium, Iron) and put them in 'micros' object with unit suffixes.\n"
        "5. Return STRICT JSON."
    )


def build_user_prompt_parse(raw_text: str) -> str:
    return (
        "Raw OCR text:\n" + raw_text + "\n\n"
        "Output format (STRICT JSON only):\n"
        "{\n"
        '  "ingredients_plain_text": "...",\n'
        '  "nutrition_data": {\n'
        '    "basis": "100ml" (The text you extracted from),\n'
        '    "is_normalized_100g": true (if 100g/ml extracted) OR false,\n'
        '    "values": {\n'
        '       "energy_kcal": number|null,\n'
        '       "fat_total_g": number|null,\n'
        '       "fat_saturated_g": number|null,\n'
        '       "fat_trans_g": number|null,\n'
        '       "carbohydrate_g": number|null,\n'
        '       "sugar_g": number|null,\n'
        '       "fiber_g": number|null,\n'
        '       "protein_g": number|null,\n'
        '       "salt_g": number|null,\n'
        '       "micros": { "calcium_mg": number } (or null)\n'
        "    }\n"
        "  }\n"
        "}"
    )


def build_system_prompt_unified(language: str = "en") -> str:
    """Build system prompt for unified analysis."""
    lang_name = _get_language_name(language)
    return (
        "You are a nutrition label analysis assistant. Input is unstructured OCR text.\n\n"
        "TASKS:\n"
        "1. Extract ingredients list (array of strings).\n"
        "2. Extract nutrition data. ***PRIORITY RULE***: If text contains both '100g/ml' and 'Portion' values, "
        "YOU MUST EXTRACT THE 100g/ml VALUES and IGNORE the portion values. "
        "Only fallback to portion values if 100g/ml is missing.\n"
        "3. Classify each ingredient's risk level ('Low', 'Medium', 'High') based on the user's health profile.\n"
        "4. Write a summary explanation.\n\n"
        "*** RISK ASSESSMENT PRINCIPLES ***\n"
        "You will receive the user's health profile including:\n"
        "- Allergies: Ingredients matching allergies are ALWAYS 'High' risk\n"
        "- Dietary preferences: Evaluate if ingredients conflict (e.g., animal products for vegans, pork for halal/kosher)\n"
        "- Health conditions: Evaluate nutrition values (e.g., high sugar for diabetes, high salt for hypertension)\n\n"
        "Use your knowledge to interpret ANY dietary preference, health condition, or allergy.\n"
        "Mark ingredients as 'High' risk if they clearly conflict with the user's profile.\n"
        "Mark as 'Medium' if there are moderate concerns.\n"
        "Mark as 'Low' if safe for the user.\n\n"
        "DATA STRUCTURE:\n"
        "- 'nutrition_data': { 'basis': str, 'is_normalized_100g': bool, 'values': {...} }\n"
        "- 'values' keys: energy_kcal, fat_total_g, sugar_g, salt_g, etc.\n"
        "- 'micros': Object for vitamins/minerals (e.g. iron_mg). Null if none.\n\n"
        f"*** CRITICAL LANGUAGE REQUIREMENT ***\n"
        f"You MUST write the following fields in {lang_name}:\n"
        f"- Ingredient names in the 'ingredients' array: {lang_name}\n"
        f"- summary_explanation field: {lang_name}\n"
        f"Risk levels MUST remain in English ('Low', 'Medium', 'High').\n\n"
        "Return STRICT JSON."
    )


def build_user_prompt_unified(
    raw_text: str, profile_text: str, language: str = "en"
) -> str:
    lang_name = _get_language_name(language)
    return (
        profile_text
        + "Raw OCR text:\n"
        + raw_text
        + "\n\nEvaluate ALL ingredients and nutrition values against the user's health profile above. "
        + "Use your knowledge to determine conflicts and risks.\n"
        + "The 'summary_risk' should reflect the highest risk level found.\n\n"
        + f"CRITICAL: Write ingredient names and summary_explanation in {lang_name}.\n\n"
        + "Output format (STRICT JSON):\n"
        + "{\n"
        + f'  "ingredients": ["Ingredient1", "Ingredient2", ...] (in {lang_name}),\n'
        + '  "nutrition_data": {\n'
        + '    "basis": "100ml",\n'
        + '    "is_normalized_100g": true,\n'
        + '    "values": {\n'
        + '       "energy_kcal": number|null,\n'
        + '       "fat_total_g": number|null,\n'
        + '       "fat_saturated_g": number|null,\n'
        + '       "fat_trans_g": number|null,\n'
        + '       "carbohydrate_g": number|null,\n'
        + '       "sugar_g": number|null,\n'
        + '       "fiber_g": number|null,\n'
        + '       "protein_g": number|null,\n'
        + '       "salt_g": number|null,\n'
        + '       "micros": { "calcium_mg": 120 } (or null)\n'
        + "    }\n"
        + "  },\n"
        + '  "risks": {"IngredientName": "Medium", "AnotherIngredient": "High"} (keys in '
        + lang_name
        + ", values in English),\n"
        + f'  "summary_explanation": "... (MUST be in {lang_name})",\n'
        + '  "summary_risk": "High" (in English)\n'
        + "}"
    )


def build_system_prompt_risk(language: str = "en") -> str:
    lang_name = _get_language_name(language)
    return (
        "You are a nutrition safety assistant. Classify ingredient risks as 'Low', 'Medium', or 'High'.\n\n"
        "You will receive the user's health profile including:\n"
        "- Allergies: Ingredients matching allergies are ALWAYS 'High' risk\n"
        "- Dietary preferences: Use your knowledge to identify conflicts (e.g., animal products for vegans)\n"
        "- Health conditions: Consider how ingredients might affect these conditions\n\n"
        "Use your knowledge to interpret ANY dietary preference, health condition, or allergy.\n"
        "Mark ingredients as 'High' if they clearly conflict with the user's profile.\n"
        "Mark as 'Medium' if there are moderate concerns.\n"
        "Mark as 'Low' if safe for the user.\n\n"
        f"CRITICAL: Ingredient names in the output object keys MUST be in {lang_name}.\n"
        f"Risk level values MUST remain in English ('Low', 'Medium', 'High')."
    )


def build_user_prompt_risk(ingredients: List[str], profile_text: str) -> str:
    return (
        profile_text
        + "Ingredients list (JSON array):\n"
        + json.dumps(ingredients, ensure_ascii=False)
    )
