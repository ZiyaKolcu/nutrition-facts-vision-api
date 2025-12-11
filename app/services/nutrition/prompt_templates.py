"""Prompt builders for nutrition parsing using Few-Shot Learning strategy."""

from __future__ import annotations
import json
from typing import List


def _get_language_name(language_code: str) -> str:
    """Convert language code to language name."""
    return "Turkish" if language_code.lower() == "tr" else "English"


# --- FEW SHOT EXAMPLES (REAL TURKISH FOOD LABELS) ---
FEW_SHOT_EXAMPLES = """
=== EXAMPLE 1: COMPLETE TURKISH LABEL (Ingredients + Nutrition) ===

INPUT OCR (Noisy, mixed Turkish/English):
"İçindekiler: Buğday unu(gluten), me Suyu, maya, bitkisel yağ (değişen miktarlarda palm, pamuk, ayçiçek), şeker, emülgatör (sodyum stearok2 laktilat), tuz, gluten, kouyucu (kalsiyum propiyonat)
ENERJİ VE BESİN ÖĞELERİ 100 g için
Enerji(Kcal/kj) 259kcal/1095 kj
Yağ(g) 3.2
Doymuş yağ(g) 1.2
Karbonhidrat (g) 46.6
Şekerler(g) 2.8
Lif (g) 3.1
Protein (g) 9.5
Tuz (g) 0.9"

THINKING PROCESS:
1. INGREDIENTS SECTION: Found "İçindekiler:" - extract everything after it until nutrition table starts
2. Clean OCR errors: "me Suyu" → "su", "kouyucu" → "koruyucu", "stearok2" → "stearoil"
3. Parse ingredients list: buğday unu, su, maya, bitkisel yağ (palm, pamuk, ayçiçek), şeker, emülgatör (sodyum stearoil laktilat), tuz, gluten, koruyucu (kalsiyum propiyonat)
4. NUTRITION SECTION: Found "100 g için" - this is the standard basis, use it
5. Extract all nutrition values from the table
6. Energy: Both kJ (1095) and kcal (259) given - use kcal value (259)

OUTPUT JSON:
{
  "_thinking_process": "Found ingredients after 'İçindekiler:' keyword. Corrected OCR errors. Found nutrition table with '100 g için' basis. Extracted all macro values.",
  "ingredients_plain_text": "buğday unu (gluten), su, maya, bitkisel yağ (palm, pamuk, ayçiçek), şeker, emülgatör (sodyum stearoil laktilat), tuz, gluten, koruyucu (kalsiyum propiyonat)",
  "nutrition_data": {
    "basis": "100g",
    "is_normalized_100g": true,
    "values": {
      "energy_kcal": 259,
      "fat_total_g": 3.2,
      "fat_saturated_g": 1.2,
      "fat_trans_g": null,
      "carbohydrate_g": 46.6,
      "sugar_g": 2.8,
      "fiber_g": 3.1,
      "protein_g": 9.5,
      "salt_g": 0.9,
      "micros": null
    }
  }
}

=== EXAMPLE 2: PRIORITY RULE (100ml vs Portion) ===

INPUT OCR:
"İçindekiler: su, portakal suyu konsantresi, şeker, karbondioksit, C vitamini
Enerji ve Besin Öğeleri
100 ml için: Enerji: 127 kJ /30 kcal, Yağ: 0g, Karbonhidrat: 7,3 g, Şekerler: 7,3 g, Protein: 0g, Tuz: 0,02g
1 porsiyon için (250 ml): Enerji: 318 kJ/75 kcal, Karbonhidrat: 18,3 g, Şekerler: 18,3 g, Tuz: 0,05 g"

THINKING PROCESS:
1. INGREDIENTS: Extract from "İçindekiler:" section
2. NUTRITION: Found TWO columns - "100 ml için" and "1 porsiyon için (250 ml)"
3. PRIORITY RULE: ALWAYS use "100 ml" or "100 g" column when available. IGNORE portion column.
4. Extract values from "100 ml için" only
5. Energy: 127 is kJ, 30 is kcal → use 30

OUTPUT JSON:
{
  "_thinking_process": "Found ingredients list. Found two nutrition columns: 100ml and portion. Applied PRIORITY RULE: using 100ml column only, ignoring portion.",
  "ingredients_plain_text": "su, portakal suyu konsantresi, şeker, karbondioksit, C vitamini",
  "nutrition_data": {
    "basis": "100ml",
    "is_normalized_100g": true,
    "values": {
      "energy_kcal": 30,
      "fat_total_g": 0,
      "fat_saturated_g": null,
      "fat_trans_g": null,
      "carbohydrate_g": 7.3,
      "sugar_g": 7.3,
      "fiber_g": null,
      "protein_g": 0,
      "salt_g": 0.02,
      "micros": null
    }
  }
}

=== EXAMPLE 3: LOGIC CHECK & DECIMAL FIX ===

INPUT OCR:
"İçindekiler: Şeker, Bitkisel Yağlar, FINDIK (%16), Kakao Tozu
100g için: Enerji: 2240/535 kj/kcal, Yağ: 30,5g, Doymuş Yağ: 6,4g, Karbonhidrat: 49,8g, Şeker: 58,1g, Protein: 8,2g, Tuz: 02g"

THINKING PROCESS:
1. INGREDIENTS: Clean and extract
2. NUTRITION: Extract from "100g için"
3. LOGIC CHECK FAILED: Sugar (58.1g) > Carbohydrate (49.8g) - IMPOSSIBLE!
4. CORRECTION: OCR likely swapped Carb and Sugar values. Swap them: Carb=58.1, Sugar=49.8
5. DECIMAL FIX: "02g" for salt is likely "0.2g" (missing decimal point)
6. Energy: 2240 is kJ, 535 is kcal → use 535

OUTPUT JSON:
{
  "_thinking_process": "Found ingredients. Extracted nutrition from 100g column. LOGIC ERROR DETECTED: Sugar > Carb is impossible. SWAPPED values. Fixed salt decimal: 02g → 0.2g",
  "ingredients_plain_text": "şeker, bitkisel yağlar, fındık (%16), kakao tozu",
  "nutrition_data": {
    "basis": "100g",
    "is_normalized_100g": true,
    "values": {
      "energy_kcal": 535,
      "fat_total_g": 30.5,
      "fat_saturated_g": 6.4,
      "fat_trans_g": null,
      "carbohydrate_g": 58.1,
      "sugar_g": 49.8,
      "fiber_g": null,
      "protein_g": 8.2,
      "salt_g": 0.2,
      "micros": null
    }
  }
}

=== EXAMPLE 4: MISSING FAT_TOTAL (Common OCR Issue) ===

INPUT OCR:
"İçindekiler: Buğday unu, şeker, yumurta, palm yağı
Enerji ve Besin Öğeleri (100g): Enerji: 1644/392 kJ/kcal, Doymuş yağ: 30g, Karbonhidrat: 48g, Şeker: 27g, Protein: 19g, Tuz: 1.1g"

THINKING PROCESS:
1. INGREDIENTS: Extract and clean
2. NUTRITION: Extract from 100g column
3. MISSING DATA: "Yağ" (total fat) is NOT listed, but "Doymuş yağ" (saturated fat) is 30g
4. INFERENCE: Total fat MUST be >= Saturated fat. Since saturated=30g and product contains "palm yağı", total fat is likely missing from OCR
5. SOLUTION: Set fat_total_g to null (we cannot infer it accurately)

OUTPUT JSON:
{
  "_thinking_process": "Found ingredients. Nutrition table missing 'Yağ' (total fat) but has saturated fat. Cannot infer total fat accurately, setting to null.",
  "ingredients_plain_text": "buğday unu, şeker, yumurta, palm yağı",
  "nutrition_data": {
    "basis": "100g",
    "is_normalized_100g": true,
    "values": {
      "energy_kcal": 392,
      "fat_total_g": null,
      "fat_saturated_g": 30,
      "fat_trans_g": null,
      "carbohydrate_g": 48,
      "sugar_g": 27,
      "fiber_g": null,
      "protein_g": 19,
      "salt_g": 1.1,
      "micros": null
    }
  }
}
"""


def build_system_prompt_parse() -> str:
    return (
        "You are an expert Turkish Food Label Parser AI specialized in extracting structured data from noisy OCR text.\n\n"
        "=== YOUR TASK ===\n"
        "Extract TWO things from Turkish food labels:\n"
        "1. INGREDIENTS LIST (İçindekiler) - The complete comma-separated list\n"
        "2. NUTRITION DATA (Besin Değerleri) - Macro nutrients from the standard 100g/100ml column\n\n"
        "=== LEARN FROM EXAMPLES ===\n"
        "Study these real Turkish food label examples carefully. Pay attention to:\n"
        "- How to find and extract ingredients\n"
        "- How to handle OCR errors\n"
        "- How to apply the PRIORITY RULE (100g/ml vs portion)\n"
        "- How to detect and fix logic errors (Sugar > Carb)\n"
        "- How to handle missing values\n\n"
        f"{FEW_SHOT_EXAMPLES}\n\n"
        "=== CRITICAL RULES ===\n\n"
        "**INGREDIENTS EXTRACTION:**\n"
        "1. Look for keywords: 'İçindekiler:', 'Ingredients:', 'İçerik:', 'Tarkibi:', 'Composition:'\n"
        "2. Extract everything after the keyword until you hit nutrition table or other section\n"
        "3. Clean OCR errors: Fix common Turkish character mistakes (ı→i, ş→s, ğ→g, ö→o, ü→u, ç→c)\n"
        "4. Keep Turkish ingredient names (do NOT translate to English)\n"
        "5. Preserve percentages and details in parentheses: 'fındık (%16)', 'bitkisel yağ (palm, ayçiçek)'\n"
        "6. Return as comma-separated plain text string\n"
        '7. If ingredients section is completely missing or unreadable, return empty string ""\n\n'
        "**NUTRITION EXTRACTION:**\n"
        "1. PRIORITY RULE: If '100g' or '100ml' column exists, use ONLY that column. IGNORE 'Porsiyon'/'Portion'/'Serving' columns completely.\n"
        "2. Look for keywords: '100 g için', '100 ml için', 'Per 100g', 'Per 100ml', '100g da'\n"
        "3. Energy: ALWAYS extract kcal (not kJ). If you see '180 kJ / 43 kcal', use 43. If only kJ given, convert (kJ ÷ 4.184 ≈ kcal)\n"
        "4. Extract these fields (set to null if not found):\n"
        "   - energy_kcal (required)\n"
        "   - fat_total_g (Yağ / Fat / Toplam Yağ)\n"
        "   - fat_saturated_g (Doymuş Yağ / Saturated Fat)\n"
        "   - fat_trans_g (Trans Yağ / Trans Fat)\n"
        "   - carbohydrate_g (Karbonhidrat / Carbohydrate)\n"
        "   - sugar_g (Şeker / Şekerler / Sugar / Sugars)\n"
        "   - fiber_g (Lif / Fiber / Posa)\n"
        "   - protein_g (Protein / Protéin)\n"
        "   - salt_g (Tuz / Salt / Sodium as salt)\n\n"
        "**LOGIC CHECKS (CRITICAL!):**\n"
        "1. Carbohydrate >= Sugar (sugar is subset of carbs). If Sugar > Carb, SWAP them.\n"
        "2. Total Fat >= Saturated Fat. If Saturated > Total, there's an OCR error.\n"
        "3. Salt is usually 0-5g. If you see '18g' salt, it's likely '1.8g' (missing decimal).\n"
        "4. Energy is usually 0-900 kcal per 100g. If > 1000, it's probably kJ not kcal.\n\n"
        "**DECIMAL FIXES:**\n"
        "- '02g' or '01g' → likely '0.2g' or '0.1g'\n"
        "- '15g' salt → likely '1.5g'\n"
        "- '180 kJ / 43 kcal' → use 43 (kcal)\n\n"
        "**OUTPUT FORMAT:**\n"
        "Return STRICT JSON with this exact schema:\n"
        "{\n"
        '  "_thinking_process": "Explain your extraction logic, any corrections made, column selection",\n'
        '  "ingredients_plain_text": "comma, separated, ingredient, list",\n'
        '  "nutrition_data": {\n'
        '    "basis": "100g" or "100ml",\n'
        '    "is_normalized_100g": true,\n'
        '    "values": {\n'
        '      "energy_kcal": number,\n'
        '      "fat_total_g": number or null,\n'
        '      "fat_saturated_g": number or null,\n'
        '      "fat_trans_g": number or null,\n'
        '      "carbohydrate_g": number or null,\n'
        '      "sugar_g": number or null,\n'
        '      "fiber_g": number or null,\n'
        '      "protein_g": number or null,\n'
        '      "salt_g": number or null,\n'
        '      "micros": null\n'
        "    }\n"
        "  }\n"
        "}\n\n"
        "IMPORTANT: Always include '_thinking_process' to show your reasoning. This helps debug extraction issues."
    )


def build_user_prompt_parse(raw_text: str) -> str:
    return (
        "=== RAW OCR TEXT FROM TURKISH FOOD LABEL ===\n"
        f"{raw_text}\n\n"
        "=== YOUR TASK ===\n"
        "1. Extract INGREDIENTS: Find 'İçindekiler:' section, clean OCR errors, return as comma-separated string\n"
        "2. Extract NUTRITION: Find '100g' or '100ml' column, extract all macro values, apply logic checks\n"
        "3. Return STRICT JSON following the exact schema from examples\n\n"
        "REMEMBER:\n"
        "- Use '100g/ml' column if available (IGNORE portion column)\n"
        "- Fix OCR errors (spelling, decimals)\n"
        "- Apply logic checks (Carb >= Sugar, Fat >= Saturated)\n"
        "- Include '_thinking_process' to explain your decisions\n"
        '- If ingredients not found, return empty string ""\n'
        "- If nutrition not found, return null for missing values\n\n"
        "Output JSON now:"
    )


def build_system_prompt_unified(language: str = "en") -> str:
    lang_name = _get_language_name(language)

    # Risk analysis examples specific to H2
    risk_examples = """
=== RISK ANALYSIS EXAMPLES ===

EXAMPLE 1: Diabetic Profile + High Sugar Product
PROFILE:
- Health Conditions: diyabet (diabetes)
- Allergies: None
- Diet: None

PRODUCT:
İçindekiler: su, şeker, portakal suyu konsantresi
Besin Değerleri: Şeker: 18.3g/100ml

RISK LOGIC:
1. "şeker" in ingredients → HIGH RISK (diabetes patient)
2. Sugar content 18.3g/100ml → Very high
3. "portakal suyu konsantresi" → Contains natural sugars → MEDIUM RISK

RISKS OUTPUT:
{
  "şeker": "High",
  "portakal suyu konsantresi": "Medium",
  "su": "Low"
}

EXAMPLE 2: Hypertension + High Salt Product
PROFILE:
- Health Conditions: hipertansiyon (hypertension)
- Allergies: None
- Diet: None

PRODUCT:
İçindekiler: buğday unu, tuz, su
Besin Değerleri: Tuz: 1.8g/100g

RISK LOGIC:
1. "tuz" in ingredients → HIGH RISK (hypertension patient)
2. Salt content 1.8g/100g → High (>1.5g threshold)
3. User has hypertension → Salt is critical

RISKS OUTPUT:
{
  "tuz": "High",
  "buğday unu": "Low",
  "su": "Low"
}

EXAMPLE 3: Keto Diet + High Carb Product
PROFILE:
- Health Conditions: None
- Allergies: None
- Diet: keto, düşük karbonhidrat

PRODUCT:
İçindekiler: buğday unu, şeker, nişasta
Besin Değerleri: Karbonhidrat: 62g/100g, Şeker: 20g/100g

RISK LOGIC:
1. "buğday unu" → HIGH CARB → HIGH RISK (keto diet)
2. "şeker" → HIGH CARB → HIGH RISK (keto diet)
3. "nişasta" → HIGH CARB → HIGH RISK (keto diet)
4. Total carbs 62g/100g → Very high for keto

RISKS OUTPUT:
{
  "buğday unu": "High",
  "şeker": "High",
  "nişasta": "High"
}

EXAMPLE 4: Vegan + Animal Products
PROFILE:
- Health Conditions: None
- Allergies: None
- Diet: vegan, bitkisel

PRODUCT:
İçindekiler: su, süt tozu, yumurta, bitkisel yağ

RISK LOGIC:
1. "süt tozu" → Animal product → HIGH RISK (vegan)
2. "yumurta" → Animal product → HIGH RISK (vegan)
3. "bitkisel yağ" → Plant-based → LOW RISK

RISKS OUTPUT:
{
  "süt tozu": "High",
  "yumurta": "High",
  "bitkisel yağ": "Low",
  "su": "Low"
}
"""

    return (
        "You are an expert Nutrition Analyst AI specialized in personalized risk assessment.\n\n"
        "=== YOUR TASK ===\n"
        "1. Extract ingredients and nutrition data\n"
        "2. Perform PERSONALIZED risk analysis based on user's health profile\n"
        "3. Provide risk level (Low/Medium/High) for EACH ingredient\n"
        "4. Generate summary explanation\n\n"
        "=== LEARN FROM PARSING EXAMPLES ===\n"
        f"{FEW_SHOT_EXAMPLES}\n\n"
        "=== LEARN FROM RISK ANALYSIS EXAMPLES ===\n"
        f"{risk_examples}\n\n"
        "=== CRITICAL RISK ASSESSMENT RULES ===\n\n"
        "**1. ALLERGENS → Always HIGH**\n"
        "   - If ingredient matches user's allergies → HIGH RISK\n"
        "   - Check for variations: 'süt', 'süt tozu', 'inek sütü' all match 'süt' allergy\n\n"
        "**2. HEALTH CONDITIONS → Specific Ingredients HIGH**\n"
        "   - DIABETES (diyabet, şeker hastalığı):\n"
        "     * şeker, glikoz, fruktoz, şurup, bal, invert şeker → HIGH\n"
        "     * High sugar content (>10g/100g) → Flag as HIGH\n"
        "   - HYPERTENSION (hipertansiyon, yüksek tansiyon):\n"
        "     * tuz, sodyum, sofra tuzu → HIGH\n"
        "     * High salt content (>1.5g/100g) → Flag as HIGH\n"
        "   - HEART DISEASE (kalp hastalığı, kardiyovasküler):\n"
        "     * trans yağ, hidrojenize yağ, doymuş yağ → HIGH\n"
        "     * palm yağı, palmiye yağı → MEDIUM\n\n"
        "**3. DIETARY PREFERENCES → Specific Ingredients HIGH**\n"
        "   - VEGAN (vegan, bitkisel):\n"
        "     * süt, yumurta, bal, jelatin, peynir, krema, tereyağı → HIGH\n"
        "     * Any animal-derived ingredient → HIGH\n"
        "   - KETO (keto, düşük karbonhidrat):\n"
        "     * şeker, un, nişasta, pirinç, makarna → HIGH\n"
        "     * High carb content (>10g/100g) → Flag as HIGH\n"
        "   - HALAL (helal):\n"
        "     * domuz yağı, domuz eti, alkol, etanol → HIGH\n\n"
        "**4. NUTRITION VALUE THRESHOLDS (per 100g/ml)**\n"
        "   - Sugar: >15g → HIGH, 10-15g → MEDIUM, <10g → LOW\n"
        "   - Salt: >1.5g → HIGH, 0.5-1.5g → MEDIUM, <0.5g → LOW\n"
        "   - Saturated Fat: >5g → HIGH, 2-5g → MEDIUM, <2g → LOW\n"
        "   - Trans Fat: >0g → HIGH (any amount is bad)\n"
        "   - Carbohydrate (for keto): >10g → HIGH, 5-10g → MEDIUM, <5g → LOW\n\n"
        "**5. DEFAULT RISK LEVELS**\n"
        "   - If ingredient doesn't match any profile concern → LOW\n"
        "   - If unsure → Use MEDIUM (not LOW)\n\n"
        "**6. IMPORTANT MATCHING RULES**\n"
        "   - Match ingredient names flexibly: 'şeker', 'kristal şeker', 'toz şeker' all contain 'şeker'\n"
        "   - Check both ingredient list AND nutrition values\n"
        "   - If ingredient is in product but not flagged, it's a MISS\n\n"
        "=== OUTPUT FORMAT ===\n"
        "Return STRICT JSON:\n"
        "{\n"
        f'  "ingredients": ["ing1", "ing2"] (in {lang_name}),\n'
        '  "nutrition_data": {\n'
        '    "basis": "100g" or "100ml",\n'
        '    "is_normalized_100g": true,\n'
        '    "values": { "energy_kcal": number, ... }\n'
        "  },\n"
        f'  "risks": {{ "ingredient_name": "High/Medium/Low" }} (ALL ingredients must have risk level, keys in {lang_name}),\n'
        f'  "summary_explanation": "Explain why product is risky for THIS user in {lang_name}",\n'
        '  "summary_risk": "High/Medium/Low"\n'
        "}\n\n"
        "CRITICAL: Assign risk level to EVERY ingredient. Don't skip any ingredient."
    )


def build_user_prompt_unified(
    raw_text: str, profile_text: str, language: str = "en"
) -> str:
    lang_name = _get_language_name(language)
    return (
        "=== USER HEALTH PROFILE ===\n"
        f"{profile_text}\n"
        "=== PRODUCT LABEL TEXT ===\n"
        f"{raw_text}\n\n"
        "=== YOUR TASK ===\n"
        "1. Extract ingredients and nutrition data from the label\n"
        "2. For EACH ingredient, determine risk level (High/Medium/Low) based on the user's profile:\n"
        "   - Check if it matches allergies → HIGH\n"
        "   - Check if it's problematic for health conditions (diabetes→sugar, hypertension→salt, etc.) → HIGH\n"
        "   - Check if it conflicts with dietary preferences (vegan→animal products, keto→carbs, etc.) → HIGH\n"
        "   - Otherwise → LOW\n"
        "3. Check nutrition values and flag ingredients if thresholds exceeded\n"
        "4. Write summary explaining why this product is risky for THIS specific user\n\n"
        "CRITICAL REMINDERS:\n"
        "- EVERY ingredient must have a risk level\n"
        "- Match flexibly: 'şeker', 'kristal şeker', 'invert şeker' all contain 'şeker'\n"
        "- For diabetes: ALL sugar-related ingredients → HIGH\n"
        "- For hypertension: ALL salt-related ingredients → HIGH\n"
        "- For keto: ALL carb-related ingredients (un, nişasta, şeker) → HIGH\n"
        "- For vegan: ALL animal products → HIGH\n\n"
        "Output STRICT JSON:\n"
        "{\n"
        f'  "ingredients": ["ing1", "ing2", ...] (in {lang_name}),\n'
        '  "nutrition_data": {\n'
        '    "basis": "100g" or "100ml",\n'
        '    "is_normalized_100g": true,\n'
        '    "values": { "energy_kcal": number, "sugar_g": number, "salt_g": number, ... }\n'
        "  },\n"
        f'  "risks": {{\n'
        f'    "ingredient1": "High",\n'
        f'    "ingredient2": "Low",\n'
        f"    ...\n"
        f"  }} (ALL ingredients, keys in {lang_name}),\n"
        f'  "summary_explanation": "Explain why risky for THIS user in {lang_name}",\n'
        '  "summary_risk": "High/Medium/Low"\n'
        "}"
    )


def build_system_prompt_risk(language: str = "en") -> str:
    lang_name = _get_language_name(language)
    return (
        f"Analyze ingredients based on the profile. Return JSON mapping ingredients to risk levels (Low/Medium/High).\n"
        f"Ingredient names in {lang_name}. Values in English."
    )


def build_user_prompt_risk(ingredients: List[str], profile_text: str) -> str:
    return f"{profile_text}\nIngredients: {json.dumps(ingredients, ensure_ascii=False)}"
