import anthropic
import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from config import CLAUDE_API_MAX_TOKENS, CLAUDE_MODEL, get_api_key, COLUMN_DESCRIPTIONS, AVAILABLE_MODELS, REQUIRED_COLUMNS, OPTIONAL_COLUMNS

class AIOptimizer:
    def __init__(self):
        self.client = None
        self.initialize_client()

    def _get_required_columns(self):
        """Get required columns from session state or use defaults"""
        if hasattr(st, 'session_state') and 'app_required_columns' in st.session_state:
            return st.session_state.app_required_columns
        return REQUIRED_COLUMNS

    def _get_optional_columns(self):
        """Get optional columns from session state or use defaults"""
        if hasattr(st, 'session_state') and 'app_optional_columns' in st.session_state:
            return st.session_state.app_optional_columns
        return OPTIONAL_COLUMNS

    def initialize_client(self) -> bool:
        api_key = get_api_key()
        if not api_key:
            # No error message needed - API key is handled through UI input
            return False

        try:
            # Show what API key we're using (masked for security)
            if hasattr(st, 'session_state'):
                masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
                st.write(f"🔑 Using API key: {masked_key}")

            self.client = anthropic.Anthropic(api_key=api_key)

            if hasattr(st, 'session_state'):
                st.write("✅ Claude API client initialized successfully")

            return True
        except Exception as e:
            if hasattr(st, 'session_state'):
                st.error(f"❌ Failed to initialize Claude API client: {str(e)}")
            return False

    def complete_bom_row(self, row_data: Dict, context_data: pd.DataFrame = None) -> Dict[str, str]:
        if not self.client:
            return {}

        # Get selected model from session state or use default
        selected_model = getattr(st.session_state, 'selected_model', CLAUDE_MODEL)
        max_tokens = AVAILABLE_MODELS.get(selected_model, {}).get('max_tokens', CLAUDE_API_MAX_TOKENS)

        prompt = self._build_completion_prompt(row_data, context_data)

        try:
            # Debug: Show API call is being made
            if hasattr(st, 'session_state') and st.session_state:
                model_name = AVAILABLE_MODELS.get(selected_model, {}).get('name', selected_model)
                st.write(f"🔗 Making API call using {model_name} for part: {row_data.get('part_number', 'Unknown')}")

            message = self.client.messages.create(
                model=selected_model,
                max_tokens=min(max_tokens, 4000),  # Cap at 4000 for completion tasks
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text

            # Debug: Show response received
            if hasattr(st, 'session_state') and st.session_state:
                st.write(f"📝 Received {len(response_text)} characters from API")

            parsed_response = self._parse_completion_response(response_text)

            # Debug: Show parsing results
            if hasattr(st, 'session_state') and st.session_state:
                if parsed_response:
                    st.write(f"✅ Parsed {len(parsed_response)} field completions")
                else:
                    st.write("⚠️ No valid completions parsed from response")
                    st.write(f"Raw response: {response_text[:200]}...")

            return parsed_response

        except Exception as e:
            error_msg = f"Error calling Claude API: {str(e)}"
            st.error(error_msg)
            # Also log the full error details
            import traceback
            st.error(f"Full error details: {traceback.format_exc()}")
            return {}

    def _build_completion_prompt(self, row_data: Dict, context_data: pd.DataFrame = None) -> str:
        # Get custom required/optional columns
        required_cols = self._get_required_columns()
        optional_cols = self._get_optional_columns()

        prompt = f"""You are an expert electronics engineer helping to complete a Bill of Materials (BOM).

Current row data:
"""

        for key, value in row_data.items():
            field_type = ""
            if key in required_cols:
                field_type = " [REQUIRED]"
            elif key in optional_cols:
                field_type = " [OPTIONAL]"

            if value and str(value).strip():
                prompt += f"- {key}{field_type}: {value}\n"
            else:
                prompt += f"- {key}{field_type}: [MISSING]\n"

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

REQUIRED FIELDS (must be filled):
"""
        for field in required_cols:
            if field in COLUMN_DESCRIPTIONS:
                prompt += f"- {field}: {COLUMN_DESCRIPTIONS[field]}\n"

        prompt += f"""
OPTIONAL FIELDS (fill if you have good information):
"""
        for field in optional_cols:
            if field in COLUMN_DESCRIPTIONS:
                prompt += f"- {field}: {COLUMN_DESCRIPTIONS[field]}\n"

        prompt += f"""
Instructions:
1. **PRIORITY: Fill ALL REQUIRED fields that are missing**
2. Fill in reasonable values for missing fields based on the part number, description, or category
3. For costs, provide realistic estimates in USD (whole numbers preferred)
4. For suppliers, suggest real electronics distributors (Digi-Key, Mouser, Arrow, etc.)
5. For manufacturers, suggest actual component manufacturers
6. Lead times should be realistic (1-30 days typically)
7. Categories should be standard electronics categories
8. Only provide values you are confident about - leave uncertain fields empty
9. Be conservative with cost estimates

Respond with a JSON object containing only the fields you want to update:
{{
    "field_name": "value",
    "another_field": "another_value"
}}

Only include fields that you are updating. Do not include fields that should remain unchanged.
Focus on completing REQUIRED fields first!
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
            # Get selected model from session state or use default
            selected_model = getattr(st.session_state, 'selected_model', CLAUDE_MODEL)
            max_tokens = AVAILABLE_MODELS.get(selected_model, {}).get('max_tokens', CLAUDE_API_MAX_TOKENS)

            message = self.client.messages.create(
                model=selected_model,
                max_tokens=min(max_tokens, 4000),  # Cap for optimization tasks
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
            part_num = row.get('part_number', 'Unknown')
            status_text.text(f"🤖 Processing row {i+1} of {len(incomplete_rows)}: {part_num}")

            row_dict = row.to_dict()
            context_df = df.drop(idx) if len(df) > 1 else None

            # Show what fields are missing for this row
            missing_fields = [col for col in row_dict.keys()
                            if pd.isna(row_dict[col]) or str(row_dict[col]).strip() == ""]
            status_text.text(f"🔍 Row {i+1} ({part_num}): Completing {len(missing_fields)} missing fields...")

            completions = self.complete_bom_row(row_dict, context_df)

            if completions:
                status_text.text(f"✅ Row {i+1} ({part_num}): AI suggested {len(completions)} completions")
                for field, value in completions.items():
                    if field in completed_df.columns and value.strip():
                        completed_df.at[idx, field] = value
            else:
                status_text.text(f"⚠️ Row {i+1} ({part_num}): No AI suggestions received")

            progress_bar.progress((i + 1) / len(incomplete_rows))

        status_text.text("Batch completion finished!")
        return completed_df

    def is_api_configured(self) -> bool:
        return self.client is not None

    def test_api_connection(self) -> bool:
        if not self.client:
            if hasattr(st, 'session_state'):
                st.error("❌ API client not initialized. Please check your API key.")
            return False

        # Get selected model from session state or use default
        selected_model = getattr(st.session_state, 'selected_model', CLAUDE_MODEL)
        model_name = AVAILABLE_MODELS.get(selected_model, {}).get('name', selected_model)

        try:
            if hasattr(st, 'session_state'):
                st.write(f"🔗 Testing connection to Claude API using {model_name}...")

            message = self.client.messages.create(
                model=selected_model,
                max_tokens=10,
                messages=[{
                    "role": "user",
                    "content": "Test connection. Reply with 'OK'."
                }]
            )

            response = message.content[0].text
            success = "OK" in response

            if hasattr(st, 'session_state'):
                if success:
                    st.write(f"✅ API response: {response}")
                else:
                    st.write(f"⚠️ Unexpected response: {response}")

            return success
        except Exception as e:
            if hasattr(st, 'session_state'):
                st.error(f"❌ API connection error: {str(e)}")
                st.error(f"Error type: {type(e).__name__}")

                # Check for common error types
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    st.error("🔑 This looks like an authentication error. Please check your API key.")
                elif "403" in str(e) or "forbidden" in str(e).lower():
                    st.error("🚫 This looks like a permissions error. Your API key may not have the right permissions.")
                elif "rate" in str(e).lower() or "429" in str(e):
                    st.error("⏰ Rate limit reached. Please wait a moment and try again.")

            return False