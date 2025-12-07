from __future__ import annotations

from typing import List, Optional, Dict, Any

from openai import (
    OpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
    BadRequestError,
)

from app.services.nutrition.openai_client import OPENAI_MODEL


def _get_language_name(language_code: str) -> str:
    """Convert language code to language name."""
    language_map = {
        "en": "English",
        "tr": "Turkish",
    }
    return language_map.get(language_code.lower(), "English")


def build_chat_system_prompt(
    product_name: str,
    ingredients: List[str],
    summary_explanation: Optional[str],
    profile_dict: Optional[dict],
    language: str = "en",
) -> str:
    """Build a concise system prompt for assistant-style replies.

    The assistant should answer briefly, focus on the scanned product, and tailor
    guidance to the provided health profile (allergies, chronic conditions, dietary preferences).

    Args:
        product_name: Name of the scanned product
        ingredients: List of ingredients
        summary_explanation: Summary of the analysis
        profile_dict: User's health profile
        language: Language code for response ('en', 'tr', etc.)
    """
    lines: List[str] = []
    lines.append("You are a concise nutrition assistant for a single scanned product.")
    lines.append("- Answer like chat: short, direct, and helpful.")
    lines.append(
        "- Restrict to this product only; avoid generic advice unless relevant."
    )
    lines.append(
        "- Consider the user's health profile carefully; if any allergy matches an ingredient, warn clearly."
    )
    lines.append(f"Product name: {product_name}")
    if ingredients:
        lines.append("Ingredients: " + ", ".join(ingredients))
    if summary_explanation:
        lines.append("Summary analysis: " + summary_explanation)
    if profile_dict:
        allergies = ", ".join(profile_dict.get("allergies", []) or [])
        conditions = ", ".join(profile_dict.get("chronic_conditions", []) or [])
        prefs = ", ".join(profile_dict.get("dietary_preferences", []) or [])
        lines.append(f"User allergies: {allergies or 'None'}")
        lines.append(f"Chronic conditions: {conditions or 'None'}")
        lines.append(f"Dietary preferences: {prefs or 'None'}")
    lines.append("Keep replies under ~2 sentences unless asked to elaborate.")
    lines.append(f"CRITICAL: You MUST respond in {_get_language_name(language)}.")
    return "\n".join(lines)


def generate_assistant_reply(oa_messages: List[Dict[str, Any]]) -> str:
    """Call OpenAI to generate a concise assistant reply. Returns a short string or 'Not sure.' on errors."""
    try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=oa_messages,
            temperature=0.2,
            max_tokens=200,
        )
        return (completion.choices[0].message.content or "").strip()
    except (
        APIError,
        APIConnectionError,
        RateLimitError,
        AuthenticationError,
        BadRequestError,
    ):
        return "Not sure."
