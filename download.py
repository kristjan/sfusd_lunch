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
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pypdf  # For reading PDF content


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


def is_pdf_for_current_month(pdf_path: Path, month: str) -> bool:
    """
    Check if the PDF content contains the specified month.
    """
    try:
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            # Check the first page for the month name
            first_page_text = reader.pages[0].extract_text()
            if month in first_page_text.lower():
                print(f"PDF '{pdf_path.name}' is for {month}.")
                return True
    except Exception as e:
        print(f"Could not read PDF {pdf_path.name}: {e}")

    print(f"PDF '{pdf_path.name}' is not for {month}.")
    return False


def download_menu():
    """
    Download all potential lunch menus and keep the one for the current month.
    """
    url = "https://www.sfusd.edu/services/health-wellness/nutrition-school-meals/menus"

    print(f"Fetching menus from: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching website: {e}")
        return False

    soup = BeautifulSoup(response.content, 'html.parser')
    current_month = get_current_month()
    print(f"Looking for {current_month} lunch menu...")

    # Find all potential menu links
    potential_links = []
    for link in soup.find_all('a', href=True):
        link_text = link.text.lower()
        if 'revolution foods hot & cold lunch menu' in link_text:
            href = link.get('href')
            # Convert to absolute URL if needed
            if href.startswith('/'):
                href = urljoin(url, href)
            potential_links.append(href)

    if not potential_links:
        print("Could not find any 'Revolution Foods' lunch menu links.")
        return False

    # Deduplicate links
    unique_links = sorted(list(set(potential_links)))
    print(f"Found {len(unique_links)} unique potential menu links.")

    # Create data and temp directories
    data_dir = Path("data")
    temp_dir = data_dir / "temp"
    temp_dir.mkdir(exist_ok=True)

    found_menu = False
    temp_files = []

    for i, link in enumerate(unique_links):
        download_url = convert_google_drive_link(link)
        temp_file = temp_dir / f"menu_{i}.pdf"
        temp_files.append(temp_file)

        print(f"\nDownloading link {i+1}/{len(unique_links)}: {download_url}")
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Check if this PDF is the one we want
            if is_pdf_for_current_month(temp_file, current_month):
                # This is the correct menu, save it and stop
                output_file = data_dir / f"{current_month}.pdf"
                temp_file.rename(output_file)
                print(f"Successfully identified and saved {output_file}")
                found_menu = True
                break

        except requests.RequestException as e:
            print(f"  -> Error downloading file: {e}")
            continue

    # Cleanup temporary files
    for f in temp_files:
        if f.exists():
            f.unlink()
    if temp_dir.exists() and not any(temp_dir.iterdir()):
        temp_dir.rmdir()

    if not found_menu:
        print(f"\nCould not find the menu for {current_month} after checking all links.")
        return False

    # On success, print the path to the final file for the orchestrator
    print(data_dir / f"{current_month}.pdf")
    return True


if __name__ == "__main__":
    success = download_menu()
    exit(0 if success else 1)