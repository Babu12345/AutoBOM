import unittest
import pandas as pd
import io
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.csv_handler import CSVHandler
from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS

class TestCSVHandler(unittest.TestCase):

    def setUp(self):
        self.handler = CSVHandler()

    def test_initialization(self):
        self.assertIsNone(self.handler.df)
        self.assertEqual(self.handler.original_columns, [])
        self.assertEqual(self.handler.mapped_columns, {})

    def test_column_mapping_suggestions(self):
        # Create test dataframe
        test_data = {
            'Part Number': ['R1', 'C1'],
            'Description': ['Resistor', 'Capacitor'],
            'Qty': [10, 5],
            'Unit Price': [0.5, 1.0]
        }
        self.handler.df = pd.DataFrame(test_data)
        self.handler.original_columns = list(test_data.keys())

        suggestions = self.handler.get_column_mapping_suggestions()

        # Should suggest mapping for part_number
        self.assertIn('part_number', suggestions)
        self.assertEqual(suggestions['part_number'], 'Part Number')

        # Should suggest mapping for description
        self.assertIn('description', suggestions)
        self.assertEqual(suggestions['description'], 'Description')

    def test_apply_column_mapping(self):
        # Create test dataframe
        test_data = {
            'Part Number': ['R1', 'C1'],
            'Description': ['Resistor', 'Capacitor'],
            'Qty': [10, 5]
        }
        self.handler.df = pd.DataFrame(test_data)

        mapping = {
            'part_number': 'Part Number',
            'description': 'Description',
            'quantity': 'Qty'
        }

        result = self.handler.apply_column_mapping(mapping)

        self.assertTrue(result)
        self.assertIn('part_number', self.handler.df.columns)
        self.assertIn('description', self.handler.df.columns)
        self.assertIn('quantity', self.handler.df.columns)

    def test_get_missing_data_summary(self):
        # Create test dataframe with missing data
        test_data = {
            'part_number': ['R1', 'C1', None],
            'description': ['Resistor', '', 'Inductor'],
            'quantity': [10, 5, 2],
            'unit_cost': [0.5, None, 1.5]
        }
        self.handler.df = pd.DataFrame(test_data)

        summary = self.handler.get_missing_data_summary()

        # Check that summary includes all columns
        self.assertIn('part_number', summary)
        self.assertIn('description', summary)
        self.assertIn('quantity', summary)
        self.assertIn('unit_cost', summary)

        # Check missing counts
        self.assertEqual(summary['part_number']['missing_count'], 1)
        self.assertEqual(summary['description']['missing_count'], 1)
        self.assertEqual(summary['quantity']['missing_count'], 0)
        self.assertEqual(summary['unit_cost']['missing_count'], 1)

    def test_get_rows_needing_completion(self):
        test_data = {
            'part_number': ['R1', 'C1', 'L1'],
            'description': ['Resistor', '', 'Inductor'],
            'quantity': [10, 5, None],
            'unit_cost': [0.5, 1.0, 1.5]
        }
        self.handler.df = pd.DataFrame(test_data)

        incomplete_rows = self.handler.get_rows_needing_completion()

        # Should return 2 rows (indices 1 and 2) that have missing data
        self.assertEqual(len(incomplete_rows), 2)
        self.assertIn(1, incomplete_rows.index)  # Row with empty description
        self.assertIn(2, incomplete_rows.index)  # Row with missing quantity

    def test_calculate_total_costs(self):
        test_data = {
            'part_number': ['R1', 'C1'],
            'quantity': [10, 5],
            'unit_cost': [0.5, 1.0]
        }
        self.handler.df = pd.DataFrame(test_data)

        result = self.handler.calculate_total_costs()

        self.assertTrue(result)
        self.assertIn('total_cost', self.handler.df.columns)
        self.assertEqual(self.handler.df.loc[0, 'total_cost'], 5.0)  # 10 * 0.5
        self.assertEqual(self.handler.df.loc[1, 'total_cost'], 5.0)  # 5 * 1.0

    def test_export_to_csv(self):
        test_data = {
            'part_number': ['R1', 'C1'],
            'description': ['Resistor', 'Capacitor']
        }
        self.handler.df = pd.DataFrame(test_data)

        csv_output = self.handler.export_to_csv()

        self.assertIsInstance(csv_output, str)
        self.assertIn('part_number', csv_output)
        self.assertIn('description', csv_output)
        self.assertIn('R1', csv_output)
        self.assertIn('Capacitor', csv_output)

if __name__ == '__main__':
    unittest.main()