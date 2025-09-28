# AI BOM Optimizer 🤖

An intelligent Bill of Materials (BOM) completion tool powered by Claude AI. This application helps engineers automatically complete missing fields in their BOMs using artificial intelligence and provides optimization suggestions.

## Description
Bill of materials completer using AI and constraint optimization to complete a spreadsheet

## Engineers
Babuabel Wanyeki (babs@wanyekitech.com)

## Features

- **AI-Powered Completion**: Uses Claude API to intelligently fill missing BOM fields
- **Smart Column Mapping**: Automatically maps uploaded file columns to standard BOM fields
- **Data Validation**: Comprehensive validation with error, warning, and info messages
- **Cost Analytics**: Visual analytics for cost distribution and supplier analysis
- **Supplier Optimization**: AI-generated suggestions for supplier consolidation
- **Export Options**: Download completed BOMs as CSV or Excel files
- **Interactive UI**: Clean, intuitive Streamlit web interface

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AutoBOM
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Create virtual environment
   python -m venv .

   # Activate virtual environment
   # On macOS/Linux:
   source bin/activate

   # On Windows:
   # Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   # Make sure virtual environment is activated
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Claude API key
   ```

5. **Get Claude API Key:**
   - Go to [Anthropic Console](https://console.anthropic.com/)
   - Create an account and generate an API key
   - Add the key to your `.env` file

## Usage

⚠️ **Important:** Always activate the virtual environment before running any commands:
```bash
# On macOS/Linux:
source bin/activate

# On Windows:
# Scripts\activate
```

1. **Start the application:**
   ```bash
   # Make sure virtual environment is activated
   streamlit run main.py
   ```

2. **Upload your BOM:**
   - Use the provided template or upload your own CSV/Excel file
   - Map columns to standard BOM fields
   - Review validation results

3. **AI Optimization:**
   - Enter your Claude API key
   - Use batch completion to fill missing fields
   - Get supplier optimization suggestions

4. **Review and Export:**
   - Edit data manually if needed
   - View cost analytics
   - Export completed BOM

## File Structure

```
AutoBOM/
├── main.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── .env.example           # Environment variables template
├── modules/
│   ├── csv_handler.py     # CSV/Excel file processing
│   ├── ai_optimizer.py    # Claude API integration
│   ├── bom_validator.py   # Data validation logic
│   └── ui_components.py   # Streamlit UI components
├── templates/
│   └── bom_template.csv   # Standard BOM template
└── sample_data/
    └── example_bom.csv    # Sample incomplete BOM
```

## BOM Template

The standard BOM includes these fields:

### Required Fields:
- `part_number`: Unique identifier for the component
- `description`: Detailed description of the component
- `quantity`: Number of units required

### Optional Fields:
- `unit_cost`: Cost per unit in USD
- `total_cost`: Total cost (quantity × unit_cost)
- `supplier`: Primary supplier name
- `manufacturer`: Component manufacturer
- `manufacturer_part_number`: Manufacturer's part number
- `lead_time_days`: Expected delivery time in days
- `category`: Component category (e.g., Resistor, Capacitor, IC)
- `datasheet_url`: Link to component datasheet
- `notes`: Additional notes or specifications

## AI Features

### Intelligent Field Completion
The AI can complete missing fields by:
- Analyzing part numbers for component information
- Estimating costs based on similar components
- Suggesting suppliers based on part categories
- Filling descriptions from part numbers
- Recommending lead times and categories

### Supplier Optimization
Get AI-powered suggestions for:
- Supplier consolidation opportunities
- Volume discount possibilities
- Alternative supplier recommendations
- Cost optimization strategies

## Requirements

- Python 3.8+
- Streamlit
- pandas
- anthropic (Claude API)
- plotly
- openpyxl
- python-dotenv

## Environment Variables

Create a `.env` file with:
```
ANTHROPIC_API_KEY=your_claude_api_key_here
```

## Testing & Demo

### Run the Demo
Try the core functionality without the full UI:
```bash
source bin/activate
python demo.py
```

The demo script demonstrates:
- Loading and validating BOM data
- Missing data analysis
- AI completion (if API key is configured)
- Export functionality

### Run Tests
Execute the test suite:
```bash
source bin/activate
python run_tests.py
```

Or run individual test modules:
```bash
source bin/activate
python -m unittest tests.test_csv_handler
python -m unittest tests.test_bom_validator
```

### Test Coverage
Current tests cover:
- CSV file handling and column mapping
- Data validation and error detection
- Missing data analysis
- Cost calculations
- Priority scoring

## File Structure (Updated)

```
AutoBOM/
├── main.py                 # Main Streamlit application
├── demo.py                 # Demo script (no UI)
├── run_tests.py           # Test runner
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── .env.example           # Environment variables template
├── modules/
│   ├── csv_handler.py     # CSV/Excel file processing
│   ├── ai_optimizer.py    # Claude API integration
│   ├── bom_validator.py   # Data validation logic
│   └── ui_components.py   # Streamlit UI components
├── tests/
│   ├── __init__.py
│   ├── test_csv_handler.py
│   └── test_bom_validator.py
├── templates/
│   └── bom_template.csv   # Standard BOM template
└── sample_data/
    └── example_bom.csv    # Sample incomplete BOM
```

## Links
https://docs.google.com/document/d/1cL7MHn83DmhX2JDQQl-k6Z9yWDF1N5ezO56tu6tilSo/edit?tab=t.0