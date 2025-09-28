import unittest
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.bom_validator import BOMValidator
from config import REQUIRED_COLUMNS

class TestBOMValidator(unittest.TestCase):

    def setUp(self):
        self.validator = BOMValidator()

    def test_validate_part_number(self):
        # Valid part number
        result = self.validator._validate_part_number("R1001", 0, pd.Series())
        self.assertIsNone(result)

        # Too short
        result = self.validator._validate_part_number("R", 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'warnings')

        # Too long
        long_part = "R" * 60
        result = self.validator._validate_part_number(long_part, 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'warnings')

        # Invalid characters
        result = self.validator._validate_part_number("R@#$%", 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'warnings')

    def test_validate_quantity(self):
        # Valid quantity
        result = self.validator._validate_quantity(10, 0, pd.Series())
        self.assertIsNone(result)

        # Negative quantity
        result = self.validator._validate_quantity(-5, 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'errors')

        # Zero quantity
        result = self.validator._validate_quantity(0, 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'errors')

        # Non-numeric quantity
        result = self.validator._validate_quantity("abc", 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'errors')

        # Very large quantity
        result = self.validator._validate_quantity(50000, 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'warnings')

    def test_validate_unit_cost(self):
        # Valid cost
        result = self.validator._validate_unit_cost(1.50, 0, pd.Series())
        self.assertIsNone(result)

        # Negative cost
        result = self.validator._validate_unit_cost(-1.50, 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'errors')

        # Zero cost
        result = self.validator._validate_unit_cost(0, 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'warnings')

        # Very high cost
        result = self.validator._validate_unit_cost(15000, 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'warnings')

        # Non-numeric cost
        result = self.validator._validate_unit_cost("expensive", 0, pd.Series())
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'errors')

    def test_validate_dataframe_missing_required_columns(self):
        # Missing required columns
        test_data = {
            'some_column': ['value1', 'value2']
        }
        df = pd.DataFrame(test_data)

        results = self.validator.validate_dataframe(df)

        # Should have errors for missing required columns
        self.assertGreater(len(results['errors']), 0)

        error_messages = [error['message'] for error in results['errors']]
        for req_col in REQUIRED_COLUMNS:
            self.assertTrue(any(req_col in msg for msg in error_messages))

    def test_validate_dataframe_complete_data(self):
        # Complete valid data
        test_data = {
            'part_number': ['R1001', 'C2001'],
            'description': ['10k Resistor', '100nF Capacitor'],
            'quantity': [10, 5],
            'unit_cost': [0.50, 1.00],
            'supplier': ['Digi-Key', 'Mouser']
        }
        df = pd.DataFrame(test_data)

        results = self.validator.validate_dataframe(df)

        # Should have no errors for complete data
        self.assertEqual(len(results['errors']), 0)

    def test_validate_row_with_missing_required_fields(self):
        row_data = pd.Series({
            'part_number': 'R1001',
            'description': '',  # Missing required field
            'quantity': 10,
            'unit_cost': 0.50
        })

        results = self.validator.validate_row(row_data, 0)

        # Should have error for missing required field
        self.assertGreater(len(results['errors']), 0)
        error_messages = [error['message'] for error in results['errors']]
        self.assertTrue(any('description' in msg for msg in error_messages))

    def test_cost_consistency_validation(self):
        row_data = pd.Series({
            'part_number': 'R1001',
            'description': 'Resistor',
            'quantity': 10,
            'unit_cost': 1.00,
            'total_cost': 5.00  # Inconsistent: should be 10.00
        })

        result = self.validator._validate_cost_consistency(row_data, 0)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'warnings')
        self.assertIn('doesn\'t match', result[1])

    def test_get_completion_priority(self):
        test_data = {
            'part_number': ['R1001', '', 'C2001'],
            'description': ['Resistor', 'Unknown', ''],
            'quantity': [10, None, 5],
            'unit_cost': [0.50, 1.00, '']
        }
        df = pd.DataFrame(test_data)

        priorities = self.validator.get_completion_priority(df)

        # Should return priority list with missing data
        self.assertGreater(len(priorities), 0)

        # First item should be a tuple with (index, description, score)
        self.assertEqual(len(priorities[0]), 3)
        self.assertIsInstance(priorities[0][0], int)  # index
        self.assertIsInstance(priorities[0][1], str)  # description
        self.assertIsInstance(priorities[0][2], (int, float))  # score

    def test_duplicate_part_number_detection(self):
        test_data = {
            'part_number': ['R1001', 'R1001', 'C2001'],  # Duplicate R1001
            'description': ['Resistor 1', 'Resistor 2', 'Capacitor'],
            'quantity': [10, 5, 3]
        }
        df = pd.DataFrame(test_data)

        warnings = self.validator._check_data_consistency(df)

        # Should detect duplicate part numbers
        self.assertGreater(len(warnings), 0)
        warning_messages = [warning['message'] for warning in warnings]
        self.assertTrue(any('Duplicate part number' in msg for msg in warning_messages))

if __name__ == '__main__':
    unittest.main()