import anthropic
import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from config import CLAUDE_API_MAX_TOKENS, CLAUDE_MODEL, get_api_key, COLUMN_DESCRIPTIONS

class AIOptimizer:
    def __init__(self):
        self.client = None
        self.initialize_client()

    def initialize_client(self) -> bool:
        api_key = get_api_key()
        if not api_key:
            return False

        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            return True
        except Exception as e:
            st.error(f"Failed to initialize Claude API client: {str(e)}")
            return False

    def complete_bom_row(self, row_data: Dict, context_data: pd.DataFrame = None) -> Dict[str, str]:
        if not self.client:
            return {}

        prompt = self._build_completion_prompt(row_data, context_data)

        try:
            message = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_API_MAX_TOKENS,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text
            return self._parse_completion_response(response_text)

        except Exception as e:
            st.error(f"Error calling Claude API: {str(e)}")
            return {}

    def _build_completion_prompt(self, row_data: Dict, context_data: pd.DataFrame = None) -> str:
        prompt = f"""You are an expert electronics engineer helping to complete a Bill of Materials (BOM).

Current row data:
"""

        for key, value in row_data.items():
            if value and str(value).strip():
                prompt += f"- {key}: {value}\n"
            else:
                prompt += f"- {key}: [MISSING]\n"

        if context_data is not None and not context_data.empty:
            prompt += f"\nContext from other BOM rows for reference:\n"
            for idx, row in context_data.head(5).iterrows():
                prompt += f"Row {idx + 1}: "
                relevant_fields = ['part_number', 'description', 'category', 'manufacturer', 'supplier']
                row_info = []
                for field in relevant_fields:
                    if field in row and pd.notna(row[field]) and str(row[field]).strip():
                        row_info.append(f"{field}={row[field]}")
                prompt += ", ".join(row_info) + "\n"

        prompt += f"""
Please complete the missing fields for this BOM row. Here are the field descriptions:

"""
        for field, desc in COLUMN_DESCRIPTIONS.items():
            prompt += f"- {field}: {desc}\n"

        prompt += f"""
Instructions:
1. Fill in reasonable values for missing fields based on the part number, description, or category
2. For costs, provide realistic estimates in USD (whole numbers preferred)
3. For suppliers, suggest real electronics distributors (Digi-Key, Mouser, Arrow, etc.)
4. For manufacturers, suggest actual component manufacturers
5. Lead times should be realistic (1-30 days typically)
6. Categories should be standard electronics categories
7. Only provide values you are confident about - leave uncertain fields empty
8. Be conservative with cost estimates

Respond with a JSON object containing only the fields you want to update:
{{
    "field_name": "value",
    "another_field": "another_value"
}}

Only include fields that you are updating. Do not include fields that should remain unchanged.
"""

        return prompt

    def _parse_completion_response(self, response: str) -> Dict[str, str]:
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                return {}

            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)

            if isinstance(parsed, dict):
                return {k: str(v) for k, v in parsed.items()}

        except (json.JSONDecodeError, ValueError):
            pass

        return {}

    def optimize_suppliers(self, df: pd.DataFrame) -> List[Dict]:
        if not self.client or df.empty:
            return []

        prompt = f"""Analyze this Bill of Materials for supplier optimization opportunities.

BOM Data:
"""

        for idx, row in df.iterrows():
            if pd.notna(row.get('part_number', '')) and pd.notna(row.get('supplier', '')):
                prompt += f"- {row['part_number']}: {row.get('description', 'N/A')} from {row.get('supplier', 'N/A')}\n"

        prompt += f"""
Please provide supplier consolidation recommendations to:
1. Reduce the number of different suppliers
2. Potentially get volume discounts
3. Simplify procurement

Respond with a JSON array of recommendations:
[
    {{
        "recommendation": "description of the recommendation",
        "affected_parts": ["part1", "part2"],
        "current_suppliers": ["supplier1", "supplier2"],
        "suggested_supplier": "consolidated supplier",
        "potential_savings": "estimated percentage or description"
    }}
]
"""

        try:
            message = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_API_MAX_TOKENS,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text
            return self._parse_optimization_response(response_text)

        except Exception as e:
            st.error(f"Error in supplier optimization: {str(e)}")
            return []

    def _parse_optimization_response(self, response: str) -> List[Dict]:
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1

            if json_start == -1 or json_end == 0:
                return []

            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)

            if isinstance(parsed, list):
                return parsed

        except (json.JSONDecodeError, ValueError):
            pass

        return []

    def batch_complete_bom(self, df: pd.DataFrame, max_rows: int = 10) -> pd.DataFrame:
        if not self.client or df.empty:
            return df

        completed_df = df.copy()
        incomplete_rows = []

        for idx, row in df.iterrows():
            has_missing = any(pd.isna(row[col]) or str(row[col]).strip() == ""
                            for col in df.columns if col in COLUMN_DESCRIPTIONS)
            if has_missing:
                incomplete_rows.append((idx, row))

        if not incomplete_rows:
            return completed_df

        incomplete_rows = incomplete_rows[:max_rows]

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, (idx, row) in enumerate(incomplete_rows):
            status_text.text(f"Processing row {i+1} of {len(incomplete_rows)}: {row.get('part_number', 'Unknown')}")

            row_dict = row.to_dict()
            context_df = df.drop(idx) if len(df) > 1 else None

            completions = self.complete_bom_row(row_dict, context_df)

            for field, value in completions.items():
                if field in completed_df.columns and value.strip():
                    completed_df.at[idx, field] = value

            progress_bar.progress((i + 1) / len(incomplete_rows))

        status_text.text("Batch completion finished!")
        return completed_df

    def is_api_configured(self) -> bool:
        return self.client is not None

    def test_api_connection(self) -> bool:
        if not self.client:
            return False

        try:
            message = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=10,
                messages=[{
                    "role": "user",
                    "content": "Test connection. Reply with 'OK'."
                }]
            )
            return "OK" in message.content[0].text
        except Exception:
            return False