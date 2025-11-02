import pandas as pd
import re
import streamlit as st
from typing import Dict, List, Tuple, Optional
from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS, ALL_COLUMNS

class BOMValidator:
    def __init__(self):
        self.validation_rules = {
            'part_number': self._validate_part_number,
            'description': self._validate_description,
            'quantity': self._validate_quantity,
            'unit_cost': self._validate_unit_cost,
            'total_cost': self._validate_total_cost,
            'supplier': self._validate_supplier,
            'manufacturer': self._validate_manufacturer,
            'manufacturer_part_number': self._validate_manufacturer_part_number,
            'lead_time_days': self._validate_lead_time,
            'category': self._validate_category,
            'datasheet_url': self._validate_url,
            'notes': self._validate_notes
        }

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

    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        validation_results = {
            'errors': [],
            'warnings': [],
            'info': []
        }

        # Use custom required columns if configured
        required_cols = self._get_required_columns()

        for column in required_cols:
            if column not in df.columns:
                validation_results['errors'].append({
                    'type': 'missing_column',
                    'column': column,
                    'message': f"Required column '{column}' is missing",
                    'row': None
                })

        for idx, row in df.iterrows():
            row_validations = self.validate_row(row, idx)
            for level in ['errors', 'warnings', 'info']:
                validation_results[level].extend(row_validations[level])

        consistency_issues = self._check_data_consistency(df)
        validation_results['warnings'].extend(consistency_issues)

        return validation_results

    def validate_row(self, row: pd.Series, row_index: int) -> Dict[str, List[Dict]]:
        results = {
            'errors': [],
            'warnings': [],
            'info': []
        }

        for column in ALL_COLUMNS:
            if column in row.index and column in self.validation_rules:
                value = row[column]
                if pd.notna(value) and str(value).strip():
                    validation_result = self.validation_rules[column](value, row_index, row)

                    if validation_result:
                        level, message = validation_result
                        results[level].append({
                            'type': 'field_validation',
                            'column': column,
                            'message': message,
                            'row': row_index,
                            'value': value
                        })

        # Use custom required columns if configured
        required_cols = self._get_required_columns()

        for req_col in required_cols:
            if req_col in row.index:
                value = row[req_col]
                if pd.isna(value) or str(value).strip() == "":
                    results['errors'].append({
                        'type': 'missing_required',
                        'column': req_col,
                        'message': f"Required field '{req_col}' is empty",
                        'row': row_index,
                        'value': None
                    })

        cost_validation = self._validate_cost_consistency(row, row_index)
        if cost_validation:
            level, message = cost_validation
            results[level].append({
                'type': 'cost_consistency',
                'column': 'total_cost',
                'message': message,
                'row': row_index,
                'value': None
            })

        return results

    def _validate_part_number(self, value: str, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        value = str(value).strip()
        if len(value) < 2:
            return ('warnings', f"Part number '{value}' seems too short")
        if len(value) > 50:
            return ('warnings', f"Part number '{value}' seems too long")
        if not re.match(r'^[A-Za-z0-9\-_\.]+$', value):
            return ('warnings', f"Part number '{value}' contains unusual characters")
        return None

    def _validate_description(self, value: str, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        value = str(value).strip()
        if len(value) < 5:
            return ('warnings', f"Description '{value}' seems too short")
        if len(value) > 200:
            return ('warnings', f"Description is very long ({len(value)} characters)")
        return None

    def _validate_quantity(self, value, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        try:
            qty = float(value)
            if qty <= 0:
                return ('errors', f"Quantity must be positive, got {qty}")
            if qty != int(qty) and qty > 1:
                return ('warnings', f"Fractional quantity {qty} - is this intentional?")
            if qty > 10000:
                return ('warnings', f"Very large quantity {qty} - please verify")
        except (ValueError, TypeError):
            return ('errors', f"Quantity '{value}' is not a valid number")
        return None

    def _validate_unit_cost(self, value, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        try:
            cost = float(value)
            if cost < 0:
                return ('errors', f"Unit cost cannot be negative, got {cost}")
            if cost == 0:
                return ('warnings', f"Unit cost is zero - is this correct?")
            if cost > 10000:
                return ('warnings', f"Very high unit cost ${cost} - please verify")
        except (ValueError, TypeError):
            return ('errors', f"Unit cost '{value}' is not a valid number")
        return None

    def _validate_total_cost(self, value, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        try:
            cost = float(value)
            if cost < 0:
                return ('errors', f"Total cost cannot be negative, got {cost}")
        except (ValueError, TypeError):
            return ('errors', f"Total cost '{value}' is not a valid number")
        return None

    def _validate_supplier(self, value: str, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        value = str(value).strip()
        if len(value) < 2:
            return ('warnings', f"Supplier name '{value}' seems too short")
        return None

    def _validate_manufacturer(self, value: str, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        value = str(value).strip()
        if len(value) < 2:
            return ('warnings', f"Manufacturer name '{value}' seems too short")
        return None

    def _validate_manufacturer_part_number(self, value: str, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        value = str(value).strip()
        if len(value) < 2:
            return ('warnings', f"Manufacturer part number '{value}' seems too short")
        return None

    def _validate_lead_time(self, value, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        try:
            days = float(value)
            if days < 0:
                return ('errors', f"Lead time cannot be negative, got {days}")
            if days > 365:
                return ('warnings', f"Very long lead time ({days} days) - please verify")
        except (ValueError, TypeError):
            return ('errors', f"Lead time '{value}' is not a valid number")
        return None

    def _validate_category(self, value: str, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        value = str(value).strip()
        common_categories = [
            'Resistor', 'Capacitor', 'Inductor', 'Diode', 'Transistor',
            'Integrated Circuit', 'IC', 'Connector', 'Switch', 'LED',
            'Crystal', 'Oscillator', 'Transformer', 'Relay', 'Fuse',
            'Battery', 'Cable', 'PCB', 'Mechanical', 'Hardware'
        ]

        if len(value) < 2:
            return ('warnings', f"Category '{value}' seems too short")

        if not any(cat.lower() in value.lower() for cat in common_categories):
            return ('info', f"Category '{value}' is not a common electronics category")

        return None

    def _validate_url(self, value: str, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        value = str(value).strip()
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(value):
            return ('warnings', f"URL '{value}' may not be valid")
        return None

    def _validate_notes(self, value: str, row_index: int, row: pd.Series) -> Optional[Tuple[str, str]]:
        value = str(value).strip()
        if len(value) > 500:
            return ('warnings', f"Notes are very long ({len(value)} characters)")
        return None

    def _validate_cost_consistency(self, row: pd.Series, row_index: int) -> Optional[Tuple[str, str]]:
        try:
            if all(col in row.index and pd.notna(row[col]) for col in ['quantity', 'unit_cost', 'total_cost']):
                quantity = float(row['quantity'])
                unit_cost = float(row['unit_cost'])
                total_cost = float(row['total_cost'])

                expected_total = quantity * unit_cost
                tolerance = 0.01

                if abs(total_cost - expected_total) > tolerance:
                    return ('warnings',
                           f"Total cost ${total_cost:.2f} doesn't match quantity × unit cost "
                           f"({quantity} × ${unit_cost:.2f} = ${expected_total:.2f})")
        except (ValueError, TypeError):
            pass

        return None

    def _check_data_consistency(self, df: pd.DataFrame) -> List[Dict]:
        warnings = []

        if 'part_number' in df.columns:
            duplicates = df[df['part_number'].duplicated() & df['part_number'].notna()]
            for idx, row in duplicates.iterrows():
                warnings.append({
                    'type': 'duplicate_part',
                    'column': 'part_number',
                    'message': f"Duplicate part number '{row['part_number']}'",
                    'row': idx,
                    'value': row['part_number']
                })

        if 'unit_cost' in df.columns:
            costs = pd.to_numeric(df['unit_cost'], errors='coerce')
            if costs.std() > costs.mean() * 2:
                warnings.append({
                    'type': 'cost_variance',
                    'column': 'unit_cost',
                    'message': "High variance in unit costs - please review for outliers",
                    'row': None,
                    'value': None
                })

        return warnings

    def get_completion_priority(self, df: pd.DataFrame) -> List[Tuple[int, str, float]]:
        priorities = []

        # Use custom columns if configured
        required_cols = self._get_required_columns()
        optional_cols = self._get_optional_columns()

        for idx, row in df.iterrows():
            missing_score = 0
            missing_fields = []

            for col in required_cols:
                if col in row.index and (pd.isna(row[col]) or str(row[col]).strip() == ""):
                    missing_score += 10
                    missing_fields.append(col)

            for col in optional_cols:
                if col in row.index and (pd.isna(row[col]) or str(row[col]).strip() == ""):
                    missing_score += 1
                    missing_fields.append(col)

            if missing_score > 0:
                priority_desc = f"Missing: {', '.join(missing_fields)}"
                priorities.append((idx, priority_desc, missing_score))

        return sorted(priorities, key=lambda x: x[2], reverse=True)