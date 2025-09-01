# SFUSD Lunch Menu Downloader

Automatically downloads the current month's lunch menu from the San Francisco Unified School District website.

## Features

- Automatically detects the current month
- Downloads the Revolution Foods Hot & Cold Lunch Menu
- Converts Google Drive links to direct download URLs
- Saves PDFs to the `data/` directory with month-based naming

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script to download the current month's menu:

```bash
source venv/bin/activate  # Activate virtual environment
python download.py
```

The script will:
1. Fetch the SFUSD menus page
2. Find the current month's lunch menu section
3. Locate the Revolution Foods Hot & Cold Lunch Menu link
4. Convert the Google Drive link to a direct download URL
5. Download the PDF to `data/<month>.pdf`

## Output

- Downloaded menus are saved in the `data/` directory
- Files are named by month (e.g., `august.pdf`, `september.pdf`)
- The script creates the `data/` directory if it doesn't exist

## Dependencies

- `requests` - HTTP library for web requests
- `beautifulsoup4` - HTML parsing library

## Notes

- Menus are typically published by the 20th of each month
- The script handles Google Drive link conversion automatically
- All SFUSD students can eat nutritious meals at no cost