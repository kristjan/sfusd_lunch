# SFUSD Lunch Menu Automator

This project automates the process of fetching the SFUSD monthly lunch menu, parsing it, and adding it to a Home Assistant calendar.

## Features

- **Smart Downloading**: Automatically finds and downloads the correct PDF menu for the current month, even when multiple months are listed on the SFUSD website.
- **AI-Powered Parsing**: Uses AI to parse the contents of the PDF, extracting dates and food items into a structured JSON format. Supports both Google Gemini (default) and OpenAI GPT-4o.
- **Home Assistant Integration**: Adds the parsed lunch menu as daily events to a specified Home Assistant calendar (`calendar.lunch`).
- **Idempotent**: The pipeline is designed to be run repeatedly. It intelligently skips expensive parsing and Home Assistant updates if the menu for the month has already been processed.
- **Fully Orchestrated**: A single script (`run.py`) manages the entire download, parse, and update workflow.

## Setup

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create an environment file:**
    Create a file named `.env` in the root of the project and add your configuration details.
    ```
    # .env
    # -- AI Provider (only one is needed) --
    GOOGLE_API_KEY="your_google_ai_api_key"
    OPENAI_API_KEY="your_openai_api_key" # Optional, if you want to use OpenAI

    # -- Home Assistant --
    HOMEASSISTANT_URL="http://your-home-assistant-ip:8123"
    HOMEASSISTANT_TOKEN="your_long_lived_access_token"
    ```

## Usage

To run the entire pipeline, simply execute the orchestration script:

```bash
./run.py
```

The script will perform the following steps:
1.  Download the latest PDF for the current month to `data/`.
2.  Check if a `data/<month>.json` file already exists.
3.  If not, it will call the default AI provider (Gemini) to parse the PDF into a new JSON file.
4.  If a new JSON file was created, it will add the events to your Home Assistant calendar.

### Using OpenAI as the Parser

By default, the script uses Google Gemini. If you prefer to use OpenAI (GPT-4o), you can switch by editing one line in the `parse_menu.py` script.

1.  Make sure your `OPENAI_API_KEY` is set in the `.env` file.
2.  Open `parse_menu.py` and find the `main()` function.
3.  Comment out the `parse_menu_with_gemini` line and uncomment the `parse_menu_with_openai` line:

    ```python
    # In parse_menu.py
    def main():
        # ...
        # menu_data = parse_menu_with_gemini(pdf_path)
        menu_data = parse_menu_with_openai(pdf_path)
        # ...
    ```

## Output

- **PDFs**: Downloaded menus are saved in the `data/` directory (e.g., `data/october.pdf`).
- **JSON**: Structured menu data is saved in the `data/` directory (e.g., `data/october.json`).
- **Home Assistant**: Events are created in the `calendar.lunch` entity.

## Notes

- Menus are typically published by the 20th of each month
- The script handles Google Drive link conversion automatically
- All SFUSD students can eat nutritious meals at no cost
- What a sorry state of affairs that it's easier to parse a PDF with an LLM than with PDF tools