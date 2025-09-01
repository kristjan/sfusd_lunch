#!/usr/bin/env python3
"""
SFUSD lunch menu PDF parser using OpenAI.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
import openai
from datetime import datetime
import sys


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

    # Create the prompt
    current_year = datetime.now().year
    prompt = f"""
    Parse this SFUSD lunch menu PDF and extract the menu data.

    Return a JSON array where each item has:
    - "date": in ISO format "yyyy-mm-dd" (e.g., "2025-08-19")
    - "food": array of food items found for that date

    Extract all dates and their corresponding food items. Split food items by natural boundaries (newlines, meal separators, etc.).

    The current year is {current_year}.
    """

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


def main():
    """Main function to parse and output menu data."""
    try:
        if len(sys.argv) != 2:
            print("Usage: python parse_menu.py <pdf_file>")
            sys.exit(1)

        pdf_path = sys.argv[1]
        menu_data = parse_menu_with_openai(pdf_path)

        # Save to JSON file - convert pdf_path to Path to get stem
        pdf_path_obj = Path(pdf_path)
        output_file = Path(f"data/{pdf_path_obj.stem}.json")
        with open(output_file, 'w') as f:
            json.dump(menu_data, f, indent=2)

        print(f"Menu data saved to {output_file}")

        # Print the first meal
        print(f"First meal: {menu_data[0]['date']} - {menu_data[0]['food']}")

    except Exception as e:
        print(f"Error parsing menu: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()