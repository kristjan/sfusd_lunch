#!/usr/bin/env python3
"""
Add SFUSD lunch menu to Home Assistant calendar.
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from dotenv import load_dotenv
import sys


def load_menu_data(json_path: str) -> List[Dict[str, str]]:
    """Load the parsed menu data from JSON file."""
    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, 'r') as f:
        return json.load(f)


def create_calendar_event(date_str: str, food_items: List[str]) -> Dict:
    """Create a Home Assistant calendar event for a lunch menu."""
    # Parse the date
    date_obj = datetime.fromisoformat(date_str)

    # Format the food items nicely with Unicode line separators
    description = "\n".join([f"- {item}" for item in food_items])

    # Create lunch time event
    start_datetime = date_obj.replace(hour=11, minute=00)
    end_datetime = date_obj.replace(hour=12, minute=00)

    return {
        "entity_id": "calendar.lunch",
        "summary": "Lunch",
        "description": description,
        "start_date_time": start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date_time": end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
    }


def add_to_homeassistant(menu_data: List[Dict[str, str]]) -> None:
    """Add menu items to Home Assistant calendar."""
    # Load environment variables
    load_dotenv()

    # Get Home Assistant configuration
    ha_url = os.getenv('HOMEASSISTANT_URL')
    ha_token = os.getenv('HOMEASSISTANT_TOKEN')

    if not ha_url or not ha_token:
        raise ValueError("HOMEASSISTANT_URL and HOMEASSISTANT_TOKEN must be set in .env")

        print(f"Adding {len(menu_data)} lunch menu events to Home Assistant...")
    print(f"Calendar: calendar.lunch")
    print(f"URL: {ha_url}")
    print()

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {ha_token}",
        "Content-Type": "application/json",
    }

    # Use the correct service API endpoint
    service_url = f"{ha_url}/api/services/calendar/create_event"

    success_count = 0
    error_count = 0

    for menu_item in menu_data:
        date_str = menu_item["date"]
        food_items = menu_item["food"]

        try:
            # Create the calendar event
            event_data = create_calendar_event(date_str, food_items)

            # Debug: print the request payload
            print(f"📤 Sending request payload:")
            print(f"   URL: {service_url}")
            print(f"   Data: {json.dumps(event_data, indent=2)}")
            print()

            # Add to Home Assistant using the service API
            response = requests.post(
                service_url,
                headers=headers,
                json=event_data,
                timeout=30
            )

            if response.status_code == 200:
                print(f"✅ Added: {date_str} - {len(food_items)} food items")
                success_count += 1
            else:
                print(f"❌ Failed: {date_str} - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                error_count += 1

        except Exception as e:
            print(f"❌ Error adding {date_str}: {e}")
            error_count += 1

    print()
    print(f"Summary: {success_count} events added successfully, {error_count} failed")
    if success_count > 0:
        print("Note: You can manually delete this test event in Home Assistant")


def main():
    """Main function to add menu to Home Assistant."""
    try:
        # Load the menu data from CLI argument
        menu_data = load_menu_data(sys.argv[1])
        print(f"Loaded {len(menu_data)} menu items from {sys.argv[1]}")

        # Add to Home Assistant
        add_to_homeassistant(menu_data)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()