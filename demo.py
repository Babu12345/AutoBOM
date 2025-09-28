#!/usr/bin/env python3
"""
AI BOM Optimizer Demo Script

This script demonstrates the core functionality of the AI BOM Optimizer
without requiring a full Streamlit interface. It shows how to:
1. Load and process a BOM file
2. Validate the data
3. Use AI to complete missing fields (if API key is provided)
4. Export the results

Run with: python demo.py
"""

import pandas as pd
import os
from dotenv import load_dotenv
from modules.csv_handler import CSVHandler
from modules.ai_optimizer import AIOptimizer
from modules.bom_validator import BOMValidator

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def main():
    print("🤖 AI BOM Optimizer - Demo Script")
    print("This demo shows the core functionality of the BOM optimizer")

    # Load environment variables
    load_dotenv()

    # Initialize components
    csv_handler = CSVHandler()
    validator = BOMValidator()
    ai_optimizer = AIOptimizer()

    print_section("1. Loading Sample BOM Data")

    # Load the sample data
    sample_file = "sample_data/example_bom.csv"
    if not os.path.exists(sample_file):
        print(f"❌ Sample file not found: {sample_file}")
        print("Please run this script from the project root directory")
        return

    # Load the sample BOM
    try:
        df = pd.read_csv(sample_file)
        csv_handler.df = df
        csv_handler.original_columns = list(df.columns)
        print(f"✅ Loaded sample BOM with {len(df)} rows and {len(df.columns)} columns")
        print("\nSample data preview:")
        print(df.head(3).to_string(index=False))
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        return

    print_section("2. Data Validation")

    # Validate the data
    validation_results = validator.validate_dataframe(df)

    errors = validation_results.get('errors', [])
    warnings = validation_results.get('warnings', [])
    info = validation_results.get('info', [])

    print(f"Validation Results:")
    print(f"  - Errors: {len(errors)}")
    print(f"  - Warnings: {len(warnings)}")
    print(f"  - Info: {len(info)}")

    if errors:
        print_subsection("Errors Found")
        for error in errors[:5]:  # Show first 5 errors
            row_info = f" (Row {error['row'] + 1})" if error['row'] is not None else ""
            print(f"  ❌ {error['message']}{row_info}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")

    if warnings:
        print_subsection("Warnings Found")
        for warning in warnings[:5]:  # Show first 5 warnings
            row_info = f" (Row {warning['row'] + 1})" if warning['row'] is not None else ""
            print(f"  ⚠️  {warning['message']}{row_info}")
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more warnings")

    print_section("3. Missing Data Analysis")

    # Analyze missing data
    missing_summary = csv_handler.get_missing_data_summary()

    print("Missing Data Summary:")
    print(f"{'Field':<20} {'Missing':<8} {'Total':<8} {'Percentage':<12} {'Required':<10}")
    print("-" * 65)

    for field, data in missing_summary.items():
        required = "✓" if data['is_required'] else "○"
        print(f"{field:<20} {data['missing_count']:<8} {data['total_count']:<8} "
              f"{data['missing_percentage']:<11.1f}% {required:<10}")

    # Get completion priorities
    priorities = validator.get_completion_priority(df)

    if priorities:
        print_subsection("Completion Priorities")
        print("Top 5 rows needing completion:")
        for i, (row_idx, description, score) in enumerate(priorities[:5]):
            print(f"  {i+1}. Row {row_idx + 1}: {description} (Score: {score})")

    print_section("4. AI Optimization")

    # Check if API key is configured
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("⚠️  No Claude API key found in environment")
        print("To test AI features:")
        print("1. Copy .env.example to .env")
        print("2. Add your Claude API key from https://console.anthropic.com/")
        print("3. Run the demo again")
        print("\nSkipping AI optimization demo...")
    else:
        print("✅ Claude API key found - testing AI features")

        # Test API connection
        if ai_optimizer.test_api_connection():
            print("✅ API connection successful")

            # Find rows that need completion
            incomplete_rows = csv_handler.get_rows_needing_completion()

            if not incomplete_rows.empty:
                print(f"\nFound {len(incomplete_rows)} rows with missing data")
                print("Demonstrating AI completion on first row...")

                # Get the first incomplete row
                first_row = incomplete_rows.iloc[0]
                row_dict = first_row.to_dict()

                print(f"\nBefore AI completion:")
                for key, value in row_dict.items():
                    if pd.isna(value) or str(value).strip() == "":
                        print(f"  {key}: [MISSING]")
                    else:
                        print(f"  {key}: {value}")

                # Use AI to complete the row (limit to avoid API costs in demo)
                try:
                    completions = ai_optimizer.complete_bom_row(row_dict)

                    if completions:
                        print(f"\nAI suggested completions:")
                        for field, value in completions.items():
                            print(f"  {field}: {value}")
                    else:
                        print("\nNo AI completions suggested")

                except Exception as e:
                    print(f"❌ AI completion failed: {e}")
            else:
                print("✅ All rows are already complete!")
        else:
            print("❌ API connection failed - check your API key")

    print_section("5. Export Results")

    # Demonstrate export functionality
    try:
        csv_output = csv_handler.export_to_csv()

        # Save to demo output file
        output_file = "demo_output.csv"
        with open(output_file, 'w') as f:
            f.write(csv_output)

        print(f"✅ Exported BOM to {output_file}")
        print(f"File size: {len(csv_output)} characters")

        # Show completion statistics
        total_rows = len(df)
        complete_rows = 0

        for _, row in df.iterrows():
            required_fields = ['part_number', 'description', 'quantity']
            if all(pd.notna(row.get(field, '')) and str(row.get(field, '')).strip() != ""
                   for field in required_fields):
                complete_rows += 1

        completion_rate = (complete_rows / total_rows) * 100 if total_rows > 0 else 0

        print(f"\nBOM Completion Statistics:")
        print(f"  Total rows: {total_rows}")
        print(f"  Complete rows: {complete_rows}")
        print(f"  Completion rate: {completion_rate:.1f}%")

    except Exception as e:
        print(f"❌ Export failed: {e}")

    print_section("Demo Complete!")

    print("🎉 Demo completed successfully!")
    print("\nNext steps:")
    print("1. Run the full Streamlit app: streamlit run main.py")
    print("2. Upload your own BOM files")
    print("3. Use AI to complete missing fields")
    print("4. Export and use your completed BOM")

    if not api_key:
        print("\n💡 Don't forget to set up your Claude API key for AI features!")

if __name__ == "__main__":
    main()