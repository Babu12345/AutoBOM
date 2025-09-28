import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple, Optional
import io
from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS, ALL_COLUMNS, COLUMN_DESCRIPTIONS

class CSVHandler:
    def __init__(self):
        self.df = None
        self.original_columns = []
        self.mapped_columns = {}

    def load_file(self, uploaded_file) -> bool:
        try:
            if uploaded_file.name.endswith('.csv'):
                self.df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(uploaded_file)
            else:
                st.error("Unsupported file format. Please upload CSV or Excel files.")
                return False

            self.original_columns = list(self.df.columns)
            return True
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return False

    def get_column_mapping_suggestions(self) -> Dict[str, str]:
        suggestions = {}
        df_columns_lower = [col.lower().replace(' ', '_').replace('-', '_')
                           for col in self.original_columns]

        for target_col in ALL_COLUMNS:
            for i, df_col in enumerate(df_columns_lower):
                if target_col in df_col or df_col in target_col:
                    suggestions[target_col] = self.original_columns[i]
                    break
        return suggestions

    def apply_column_mapping(self, column_mapping: Dict[str, str]) -> bool:
        try:
            self.mapped_columns = column_mapping
            rename_dict = {v: k for k, v in column_mapping.items() if v}
            self.df = self.df.rename(columns=rename_dict)

            for col in ALL_COLUMNS:
                if col not in self.df.columns:
                    self.df[col] = ""

            return True
        except Exception as e:
            st.error(f"Error applying column mapping: {str(e)}")
            return False

    def validate_data(self) -> Dict[str, List[str]]:
        issues = {"errors": [], "warnings": []}

        for col in REQUIRED_COLUMNS:
            if col not in self.df.columns:
                issues["errors"].append(f"Required column '{col}' is missing")
            elif self.df[col].isna().any():
                null_count = self.df[col].isna().sum()
                issues["errors"].append(f"Required column '{col}' has {null_count} empty values")

        if 'quantity' in self.df.columns:
            non_numeric = pd.to_numeric(self.df['quantity'], errors='coerce').isna().sum()
            if non_numeric > 0:
                issues["errors"].append(f"Quantity column has {non_numeric} non-numeric values")

        if 'unit_cost' in self.df.columns and not self.df['unit_cost'].isna().all():
            non_numeric = pd.to_numeric(self.df['unit_cost'], errors='coerce').isna().sum()
            if non_numeric > 0:
                issues["warnings"].append(f"Unit cost column has {non_numeric} non-numeric values")

        return issues

    def get_missing_data_summary(self) -> Dict[str, Dict]:
        summary = {}

        for col in ALL_COLUMNS:
            if col in self.df.columns:
                missing_count = self.df[col].isna().sum() + (self.df[col] == "").sum()
                total_count = len(self.df)
                missing_percentage = (missing_count / total_count) * 100

                summary[col] = {
                    "missing_count": missing_count,
                    "total_count": total_count,
                    "missing_percentage": missing_percentage,
                    "is_required": col in REQUIRED_COLUMNS,
                    "description": COLUMN_DESCRIPTIONS.get(col, "")
                }

        return summary

    def get_rows_needing_completion(self) -> pd.DataFrame:
        # Create mask with the same index as self.df
        mask = pd.Series([False] * len(self.df), index=self.df.index)

        for col in ALL_COLUMNS:
            if col in self.df.columns:
                mask |= (self.df[col].isna() | (self.df[col] == ""))

        return self.df[mask].copy()

    def update_row(self, index: int, updates: Dict[str, str]) -> bool:
        try:
            for col, value in updates.items():
                if col in self.df.columns:
                    self.df.at[index, col] = value
            return True
        except Exception as e:
            st.error(f"Error updating row: {str(e)}")
            return False

    def export_to_csv(self) -> str:
        output = io.StringIO()
        self.df.to_csv(output, index=False)
        return output.getvalue()

    def export_to_excel(self) -> bytes:
        output = io.BytesIO()
        self.df.to_excel(output, index=False, engine='openpyxl')
        return output.getvalue()

    def get_dataframe(self) -> pd.DataFrame:
        return self.df.copy() if self.df is not None else pd.DataFrame()

    def calculate_total_costs(self) -> bool:
        try:
            if 'quantity' in self.df.columns and 'unit_cost' in self.df.columns:
                self.df['quantity'] = pd.to_numeric(self.df['quantity'], errors='coerce')
                self.df['unit_cost'] = pd.to_numeric(self.df['unit_cost'], errors='coerce')
                self.df['total_cost'] = self.df['quantity'] * self.df['unit_cost']
                return True
            return False
        except Exception as e:
            st.error(f"Error calculating total costs: {str(e)}")
            return False