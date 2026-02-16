import json
import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ReferenceDataService:
    """
    A Singleton service to load and provide access to static reference data
    (additives, allergens, nutrients, etc.) from JSON files.
    This ensures data is loaded into memory only once.
    """

    _instance = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReferenceDataService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._is_initialized:
            return

        self.base_data_path = self._get_data_path()
        self.additives: Dict[str, Any] = {}
        self.allergens: Dict[str, Any] = {}
        self.nutrients: Dict[str, Any] = {}
        self.vitamins: Dict[str, Any] = {}
        self.minerals: Dict[str, Any] = {}
        self.food_groups: Dict[str, Any] = {}
        self.nova_groups: Dict[str, Any] = {}

        self._load_all_data()
        self._is_initialized = True

    def _get_data_path(self) -> str:
        """Calculates the absolute path to the 'data' directory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        data_path = os.path.join(project_root, "data")
        return data_path

    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Helper to safely load a JSON file."""
        file_path = os.path.join(self.base_data_path, filename)
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Reference data file not found: {file_path}")
                return {}

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Successfully loaded {len(data)} records from {filename}")
                return data
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return {}

    def _load_all_data(self):
        """Loads all reference JSON files into memory."""
        logger.info("Loading reference data...")
        self.additives = self._load_json_file("additives_multi.json")
        self.allergens = self._load_json_file("allergens_multi.json")
        self.nutrients = self._load_json_file("nutrients_multi.json")
        self.vitamins = self._load_json_file("vitamins_multi.json")
        self.minerals = self._load_json_file("minerals_multi.json")
        self.food_groups = self._load_json_file("food_groups_multi.json")
        self.nova_groups = self._load_json_file("nova_groups_multi.json")
        logger.info("All reference data loaded.")

    def get_additive_details(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves details for a given E-code (e.g., 'E330').
        Normalizes input to uppercase and standard format.
        """
        if not code:
            return None

        normalized_code = code.upper().replace("-", "").strip()

        if normalized_code in self.additives:
            return self.additives[normalized_code]

        return None

    def get_additive_risk_info(self, code: str) -> str:
        """Returns a formatted string about the additive's risk/category for RAG context."""
        details = self.get_additive_details(code)
        if not details:
            return ""

        name = details.get("name_en", "Unknown")
        category = details.get("functional_class", "Unknown")
        return f"{code} ({name}) is a {category}."

    def is_known_allergen(self, ingredient_name: str) -> bool:
        """
        Checks if an ingredient is a known allergen.
        This performs a basic check against the allergen keys or names.
        """
        if not ingredient_name:
            return False

        normalized_name = ingredient_name.lower().strip()

        if normalized_name in self.allergens:
            return True

        for key, data in self.allergens.items():
            if data.get("name_en", "").lower() == normalized_name:
                return True
            if data.get("name_tr", "").lower() == normalized_name:
                return True

        return False

    def get_nutrient_reference(self, nutrient_name: str) -> Optional[Dict[str, Any]]:
        """Looks up nutrient info from nutrients, vitamins, or minerals."""
        normalized_name = nutrient_name.lower().strip()

        for source in [self.nutrients, self.vitamins, self.minerals]:
            if normalized_name in source:
                return source[normalized_name]

            for key, data in source.items():
                if data.get("name_en", "").lower() == normalized_name:
                    return data

        return None


reference_data_service = ReferenceDataService()
