import os
from typing import Dict

REQUIRED_COLUMNS = [
    "part_number",
    "description",
    "quantity"
]

OPTIONAL_COLUMNS = [
    "unit_cost",
    "total_cost",
    "supplier",
    "manufacturer",
    "manufacturer_part_number",
    "lead_time_days",
    "category",
    "datasheet_url",
    "notes"
]

ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

COLUMN_DESCRIPTIONS = {
    "part_number": "Unique identifier for the component",
    "description": "Detailed description of the component",
    "quantity": "Number of units required",
    "unit_cost": "Cost per unit in USD",
    "total_cost": "Total cost (quantity × unit_cost)",
    "supplier": "Primary supplier name",
    "manufacturer": "Component manufacturer",
    "manufacturer_part_number": "Manufacturer's part number",
    "lead_time_days": "Expected delivery time in days",
    "category": "Component category (e.g., Resistor, Capacitor, IC)",
    "datasheet_url": "Link to component datasheet",
    "notes": "Additional notes or specifications"
}

CLAUDE_API_MAX_TOKENS = 4000
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

# Available Claude models with descriptions
AVAILABLE_MODELS = {
    "claude-3-5-sonnet-20241022": {
        "name": "Claude 3.5 Sonnet (Latest)",
        "description": "Most capable model, best for complex reasoning and analysis",
        "max_tokens": 8192,
        "recommended": True
    },
    "claude-3-5-haiku-20241022": {
        "name": "Claude 3.5 Haiku",
        "description": "Fastest model, good for simple tasks and cost efficiency",
        "max_tokens": 8192,
        "recommended": False
    },
    "claude-3-opus-20240229": {
        "name": "Claude 3 Opus",
        "description": "Most powerful model, best for complex analysis (higher cost)",
        "max_tokens": 4096,
        "recommended": False
    },
    "claude-3-sonnet-20240229": {
        "name": "Claude 3 Sonnet (Legacy)",
        "description": "Previous generation, may not be available",
        "max_tokens": 4096,
        "recommended": False
    }
}

def get_api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "")

def fetch_available_models(api_key: str = None) -> Dict:
    """Fetch available models from Anthropic API"""
    import anthropic
    import time

    if not api_key:
        api_key = get_api_key()

    if not api_key:
        # Return fallback static models if no API key
        return AVAILABLE_MODELS

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Use the models API endpoint
        models_response = client.models.list()

        dynamic_models = {}

        for model in models_response.data:
            model_id = model.id

            # Skip non-Claude models or models we can't use for completion
            if not model_id.startswith('claude-'):
                continue

            # Determine model capabilities and description
            description = "Claude model"
            max_tokens = 4096
            recommended = False

            # Parse model info from ID
            if '3-5-sonnet' in model_id:
                description = "Most capable model, best for complex reasoning and analysis"
                max_tokens = 8192
                recommended = True
                name = "Claude 3.5 Sonnet"
            elif '3-5-haiku' in model_id:
                description = "Fastest model, good for simple tasks and cost efficiency"
                max_tokens = 8192
                name = "Claude 3.5 Haiku"
            elif '3-opus' in model_id:
                description = "Most powerful model, best for complex analysis (higher cost)"
                max_tokens = 4096
                name = "Claude 3 Opus"
            elif '3-sonnet' in model_id:
                description = "Balanced model for general use"
                max_tokens = 4096
                name = "Claude 3 Sonnet"
            elif '3-haiku' in model_id:
                description = "Fast and cost-effective model"
                max_tokens = 4096
                name = "Claude 3 Haiku"
            else:
                # Generic naming for unknown models
                name = f"Claude {model_id.replace('claude-', '').replace('-', ' ').title()}"

            # Add version date if present
            if model_id.count('-') >= 3:
                date_part = model_id.split('-')[-1]
                if len(date_part) == 8 and date_part.isdigit():
                    name += f" ({date_part[:4]}-{date_part[4:6]}-{date_part[6:8]})"

            dynamic_models[model_id] = {
                "name": name,
                "description": description,
                "max_tokens": max_tokens,
                "recommended": recommended
            }

        # If we got models, return them, otherwise fallback
        return dynamic_models if dynamic_models else AVAILABLE_MODELS

    except Exception as e:
        # If API call fails, return static fallback
        print(f"Failed to fetch models from API: {e}")
        return AVAILABLE_MODELS

def validate_environment() -> Dict[str, bool]:
    return {
        "api_key": bool(get_api_key()),
        "required_packages": True
    }