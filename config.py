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
CLAUDE_MODEL = "claude-3-sonnet-20240229"

def get_api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "")

def validate_environment() -> Dict[str, bool]:
    return {
        "api_key": bool(get_api_key()),
        "required_packages": True
    }