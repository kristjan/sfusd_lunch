#!/usr/bin/env python3
"""
SFUSD lunch menu PDF parser using OpenAI and Gemini.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
import openai
import google.generativeai as genai
import mimetypes
from datetime import datetime
import sys


def get_prompt() -> str:
    """Return the prompt for the AI."""
    current_year = datetime.now().year
    return f"""
    Parse this SFUSD lunch menu PDF and extract the menu data.

    Return a JSON array where each item has:
    - "date": in ISO format "yyyy-mm-dd" (e.g., "2025-08-19")
    - "food": array of food items found for that date

    Extract all dates and their corresponding food items. Split food items by natural boundaries (newlines, meal separators, etc.).

    The current year is {current_year}.
    """


def parse_menu_with_openai(pdf_path: str) -> List[Dict[str, str]]:
    """Parse the menu PDF using OpenAI."""
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Load environment variables from .env file
    load_dotenv()

    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)

    prompt = get_prompt()

    try:
        # First create the file
        with open(pdf_path, "rb") as file:
            file_response = client.files.create(
                file=file,
                purpose="assistants"
            )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "file",
                            "file": {"file_id": file_response.id}
                        }
                    ]
                }
            ],
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        # Extract and parse the JSON response
        content = response.choices[0].message.content
        menu_data = json.loads(content)

        # Ensure it's a list
        if isinstance(menu_data, dict) and 'menu' in menu_data:
            menu_data = menu_data['menu']
        elif not isinstance(menu_data, list):
            raise ValueError("OpenAI response is not in expected format")

        return menu_data

    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        raise


def parse_menu_with_gemini(pdf_path: str) -> List[Dict[str, str]]:
    """Parse the menu PDF using Gemini."""
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Load environment variables from .env file
    load_dotenv()

    # Check for Google API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    genai.configure(api_key=api_key)

    prompt = get_prompt()

    try:
        # Upload the PDF file
        mime_type, _ = mimetypes.guess_type(pdf_path)
        if not mime_type:
            mime_type = "application/pdf"

        uploaded_file = genai.upload_file(path=pdf_path, display_name=pdf_path.name, mime_type=mime_type)

        # Create the model instance and generate content
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            [prompt, uploaded_file],
            generation_config={"response_mime_type": "application/json"}
        )

        # Extract and parse the JSON response
        menu_data = json.loads(response.text)

        # Ensure it's a list
        if isinstance(menu_data, dict) and 'menu' in menu_data:
            menu_data = menu_data['menu']
        elif not isinstance(menu_data, list):
            raise ValueError("Gemini response is not in expected format")

        return menu_data

    except Exception as e:
        print(f"Error calling Gemini: {e}")
        raise


def main():
    """Main function to parse and output menu data."""
    try:
        if len(sys.argv) != 2:
            print("Usage: python parse_menu.py <pdf_file>")
            sys.exit(1)

        pdf_path = sys.argv[1]
        # Uncomment one of the following lines to use the desired parser
        # menu_data = parse_menu_with_openai(pdf_path)
        menu_data = parse_menu_with_gemini(pdf_path)

        # Save to JSON file - convert pdf_path to Path to get stem
        pdf_path_obj = Path(pdf_path)
        output_file = Path(f"data/{pdf_path_obj.stem}.json")
        with open(output_file, 'w') as f:
            json.dump(menu_data, f, indent=2)

        # For the orchestrator, print the path of the output file
        print(output_file)

    except Exception as e:
        print(f"Error parsing menu: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()