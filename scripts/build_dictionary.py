#!/usr/bin/env python3
"""
build_dictionary.py (UNIVERSAL CHUNK PARSER)

Robustly parses Open Food Facts taxonomy files by splitting content into chunks (paragraphs).
Handles mixed formats (bracket headers vs plain text headers) using per-file priority rules.
Generates clean JSON lookup tables mapping synonyms to a single Canonical Code.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
RAW_FILES_DIR = BASE_DIR / "../raw_files"
OUTPUT_DIR = BASE_DIR / "../data"
LOG_FILE = BASE_DIR / "build_dictionary.log"

# Generic terms to exclude from the dictionary to prevent over-matching
GENERIC_TERMS = {
    "vitamin",
    "mineral",
    "additive",
    "additive ingredient",
    "colour",
    "color",
    "colorant",
    "nutrient",
    "nutrient value",
    "allergen",
    "food",
    "ingredient",
    "alias",
    "unknown",
    "not applicable",
    "none",
    "allergens-free",
    "without allergens",
    "1",
    "2",
    "3",
    "4",
}

# Prefixes that indicate a line is metadata or comment, not a synonym
IGNORE_STARTS = (
    "#",
    "//",
    "http",
    "https",
    "www",
    "description:",
    "stopwords:",
    "synonyms:",
    "wikidata:",
    "wikipedia:",
    "reference:",
    "date:",
    "uuid:",
)

# Configuration per file:
# 'priorities': List of prefixes to look for to identify the Canonical ID line.
#               The parser checks them in order.
FILE_CONFIGS = {
    "additives.txt": {"priorities": ["< en:", "en:"], "output": "additives_multi.json"},
    "minerals.txt": {"priorities": ["< en:", "en:"], "output": "minerals_multi.json"},
    "vitamins.txt": {"priorities": ["< en:", "en:"], "output": "vitamins_multi.json"},
    "food_groups.txt": {
        "priorities": [
            "en:"
        ],  # Ignore < en: parent groups, capture the child group name
        "output": "food_groups_multi.json",
    },
    "nova_groups.txt": {"priorities": ["en:"], "output": "nova_groups_multi.json"},
    "allergens.txt": {"priorities": ["en:"], "output": "allergens_multi.json"},
    "nutrients.txt": {"priorities": ["zz:"], "output": "nutrients_multi.json"},
}

# ============================================================================
# Setup
# ============================================================================


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


logger = setup_logging()

# ============================================================================
# Helper Functions
# ============================================================================


def clean_key(text: str) -> str:
    """Normalizes a key: lowercase, stripped."""
    return text.strip().lower()


def extract_id_from_line(line: str, prefix: str) -> str:
    """
    Extracts the ID from a line based on the prefix.
    - If prefix is '< en:', ID is between 'en:' and '>' (or end of line).
    - If prefix is 'en:' or 'zz:', ID is the part after prefix (up to first comma).
    """
    if prefix == "< en:":
        # Format: < en:E100 > or < en:E100
        try:
            parts = line.split("en:", 1)[1]
            return parts.replace(">", "").strip()
        except:
            return ""

    else:
        # Format: en: E100, Curcumin
        try:
            content = line.split(prefix, 1)[1].strip()
            # ID is usually the first item before a comma
            if "," in content:
                return content.split(",", 1)[0].strip()
            return content
        except:
            return ""


# ============================================================================
# Core Parsing Logic
# ============================================================================


def parse_file_chunks(file_path: Path, priorities: List[str]) -> Dict[str, str]:
    """
    Universal parser that splits file by empty lines (chunks).
    For each chunk, it finds the ID using the priority prefixes.
    """
    lookup = {}
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return {}

    # Split by empty blocks (double newline)
    # This assumes that entries are visually separated by blank lines.
    chunks = content.split("\n\n")

    for chunk in chunks:
        lines = [l.strip() for l in chunk.split("\n") if l.strip()]
        if not lines:
            continue

        # Skip comment chunks
        if lines[0].startswith("#"):
            continue

        # 1. Identify Canonical ID
        canonical_id = None

        # Scan the chunk for the highest priority ID line
        for priority in priorities:
            for line in lines:
                if line.startswith(priority) or line.startswith(
                    priority.replace(" ", "")
                ):
                    # Handle flexible spacing like "<en:" vs "< en:"
                    # We normalize check by removing spaces in startswith check,
                    # but logic below uses strict prefix splitting.

                    # Re-verify strictly or loosely
                    if line.startswith(priority):
                        candidate = extract_id_from_line(line, priority)
                    elif line.startswith(priority.replace(" ", "")):
                        # Fallback for spacing variants
                        candidate = extract_id_from_line(
                            line, priority.replace(" ", "")
                        )
                    else:
                        candidate = ""

                    if candidate:
                        canonical_id = candidate
                        break
            if canonical_id:
                break

        if not canonical_id:
            continue

        # 2. Process Synonyms (All lines in chunk)
        # Add Canonical Self
        clean_canon = clean_key(canonical_id)
        if clean_canon and clean_canon not in GENERIC_TERMS:
            lookup[clean_canon] = canonical_id

        for line in lines:
            if line.startswith(IGNORE_STARTS):
                continue

            # Line format: "lang: val1, val2"
            if ":" in line:
                parts = line.split(":", 1)
                # Check if the part before colon is a language code (2-3 chars usually)
                # or match specific prefixes.
                # Actually, we can just split by colon.

                val_part = parts[1].strip()
                if val_part:
                    syns = [s.strip() for s in val_part.split(",")]
                    for syn in syns:
                        ck = clean_key(syn)
                        # Filter garbage
                        if not ck or len(ck) < 2 or "http" in ck or ck in GENERIC_TERMS:
                            continue

                        lookup[ck] = canonical_id

    return lookup


# ============================================================================
# Main Execution
# ============================================================================


def process_file(filename: str, config: Dict):
    file_path = RAW_FILES_DIR / filename
    if not file_path.exists():
        logger.warning(f"File not found: {filename}")
        return

    logger.info(f"Processing {filename}...")
    lookup_table = parse_file_chunks(file_path, config["priorities"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / config["output"]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(lookup_table, f, ensure_ascii=False, indent=2, sort_keys=True)

    logger.info(f"✅ Saved {config['output']} ({len(lookup_table)} entries)")


def main():
    logger.info("=" * 40)
    logger.info("   Open Food Facts Dictionary Builder   ")
    logger.info("   Mode: Universal Chunk Parser         ")
    logger.info("=" * 40)

    for filename, config in FILE_CONFIGS.items():
        process_file(filename, config)

    logger.info("\nDone. All dictionaries generated in data/")


if __name__ == "__main__":
    main()
