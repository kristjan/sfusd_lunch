#!/usr/bin/env python3
"""
SFUSD Lunch Menu Downloader

Automatically downloads the current month's lunch menu from SFUSD website.
"""

import os
import re
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


def get_current_month():
    """Get the current month name in title case."""
    return datetime.now().strftime("%B").lower()


def convert_google_drive_link(link):
    """Convert Google Drive view link to direct download link."""
    # Extract file ID from Google Drive link
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', link)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return link


def download_menu():
    """Download the current month's lunch menu."""
    url = "https://www.sfusd.edu/services/health-wellness/nutrition-school-meals/menus"

    print(f"Fetching menus from: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching website: {e}")
        return False

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the current month's lunch menu section
    current_month = get_current_month()
    print(f"Looking for {current_month} lunch menu...")

    # Look for the lunch menu section with the current month
    menu_section = None
    for section in soup.find_all(['h3', 'h4']):
        if section.text and current_month in section.text.lower() and 'lunch' in section.text.lower():
            menu_section = section
            print(f"Found menu section: {section.text.strip()}")
            break

    if not menu_section:
        print(f"Could not find {current_month} lunch menu section")
        # Debug: show all h3 and h4 elements
        print("Available sections:")
        for section in soup.find_all(['h3', 'h4']):
            if section.text:
                print(f"  - {section.text.strip()}")
        return False

    # Find the Revolution Foods Hot & Cold Lunch Menu link
    menu_link = None

    # First try to find the link within the section or nearby
    # Look for links that contain the right text
    for link in soup.find_all('a', href=True):
        link_text = link.text.lower()
        if ('revolution foods' in link_text and
            'hot & cold' in link_text and
            'lunch' in link_text):
            menu_link = link.get('href')
            print(f"Found menu link: {link_text}")
            break

    # If not found, try a broader search
    if not menu_link:
        print("Trying broader search for Revolution Foods lunch menu...")
        for link in soup.find_all('a', href=True):
            link_text = link.text.lower()
            if ('revolution foods' in link_text and 'lunch' in link_text):
                menu_link = link.get('href')
                print(f"Found alternative menu link: {link_text}")
                break

    if not menu_link:
        print("Could not find Revolution Foods Hot & Cold Lunch Menu link")
        # Debug: show all links
        print("Available links:")
        for link in soup.find_all('a', href=True):
            if link.text and ('revolution' in link.text.lower() or 'lunch' in link.text.lower()):
                print(f"  - {link.text.strip()} -> {link.get('href')}")
        return False

    # Convert to absolute URL if needed
    if menu_link.startswith('/'):
        menu_link = urljoin(url, menu_link)

    print(f"Found menu link: {menu_link}")

    # Convert Google Drive link to direct download
    download_url = convert_google_drive_link(menu_link)
    print(f"Download URL: {download_url}")

    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Download the file
    output_file = data_dir / f"{current_month}.pdf"
    print(f"Downloading to: {output_file}")

    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Successfully downloaded {output_file}")
        return True

    except requests.RequestException as e:
        print(f"Error downloading file: {e}")
        return False


if __name__ == "__main__":
    success = download_menu()
    exit(0 if success else 1)