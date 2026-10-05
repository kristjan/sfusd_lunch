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


def get_next_month():
    """Get the next month name in title case."""
    now = datetime.now()
    if now.month == 12:
        next_month_date = datetime(now.year + 1, 1, 1)
    else:
        next_month_date = datetime(now.year, now.month + 1, 1)
    return next_month_date.strftime("%B").lower()


def convert_google_drive_link(link):
    """Convert Google Drive view link to direct download link."""
    # Extract file ID from Google Drive link
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', link)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return link


MONTH_PATTERNS = {
    'january': r'\b(january|jan)\b',
    'february': r'\b(february|feb)\b',
    'march': r'\b(march|mar)\b',
    'april': r'\b(april|apr)\b',
    'may': r'\bmay\b',
    'june': r'\b(june|jun)\b',
    'july': r'\b(july|jul)\b',
    'august': r'\b(august|aug)\b',
    'september': r'\b(september|sept|sep)\b',
    'october': r'\b(october|oct)\b',
    'november': r'\b(november|nov)\b',
    'december': r'\b(december|dec)\b',
}


def is_pdf_for_month(pdf_path: Path, month: str) -> bool:
    """
    Check if the PDF content contains the specified month (full name or abbreviation).
    """
    pattern = MONTH_PATTERNS.get(month.lower(), rf"\b{re.escape(month.lower())}\b")
    try:
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            # Check all pages for the month name or abbreviation
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if re.search(pattern, page_text, re.IGNORECASE):
                    print(f"PDF '{pdf_path.name}' is for {month}.")
                    return True
    except Exception as e:
        print(f"Could not read PDF {pdf_path.name}: {e}")

    # print(f"PDF '{pdf_path.name}' is not for {month}.") # Reduce noise
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
    next_month = get_next_month()
    months_to_find = {current_month, next_month}
    print(f"Looking for menus for: {', '.join(months_to_find)}")

    # Find menu links, prioritizing Revolution Foods
    ranked_links = []
    excluded_keywords = ['supper', 'pre-k', 'allergen', 'ingredient', '2015', '2016', '2017', '2018', '2019', '2020']

    # 1. Prioritize Revolution Foods section
    rev_header = soup.find(lambda el: el.name in ['h2', 'h3', 'h4'] and 'revolution foods' in el.text.lower())
    if rev_header:
        container = rev_header.find_parent(class_=lambda c: c and 'postcard-carousel' in c) or rev_header.find_parent(class_=lambda c: c and 'postcard' in c) or rev_header.parent
        for link in container.find_all('a', href=True):
            href = link.get('href')
            if not ('drive.google.com/file' in href or href.endswith('.pdf')):
                continue
            if href.startswith('/'):
                href = urljoin(url, href)

            link_text = link.get_text().strip().lower()
            parent = link.find_parent(['p', 'li', 'div'])
            context_text = parent.get_text(' ', strip=True).lower() if parent else link_text
            full_text = f"{link_text} {context_text}"

            if any(skip in full_text for skip in excluded_keywords):
                continue

            month_match = any(m in link_text for m in months_to_find)

            if 'breakfast & lunch' in full_text or 'hot/cold' in full_text:
                rank = 1 if month_match else 2
            elif 'lunch' in full_text:
                rank = 3 if month_match else 4
            else:
                rank = 5 if month_match else 6

            ranked_links.append((rank, href))

    # 2. Fallback if no Revolution Foods links found
    if not ranked_links:
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not ('drive.google.com/file' in href or href.endswith('.pdf')):
                continue
            if href.startswith('/'):
                href = urljoin(url, href)

            link_text = link.get_text().strip().lower()
            parent = link.find_parent(['p', 'li', 'div'])
            context_text = parent.get_text(' ', strip=True).lower() if parent else link_text
            full_text = f"{link_text} {context_text}"

            if any(skip in full_text for skip in excluded_keywords):
                continue

            month_match = any(m in link_text for m in months_to_find)

            # Prioritize standard hot/cold lunch menus
            if 'hot/cold' in full_text and 'classroom' not in full_text:
                rank = 1 if month_match else 2
            elif 'breakfast & lunch' in full_text or 'lunch' in full_text:
                rank = 3 if month_match else 4
            else:
                rank = 5 if month_match else 6
            ranked_links.append((rank, href))

    if not ranked_links:
        print("Could not find any lunch menu links.")
        return False

    # Sort by rank and deduplicate preserving order
    ranked_links.sort(key=lambda x: x[0])
    seen = set()
    unique_links = []
    for _, href in ranked_links:
        if href not in seen:
            seen.add(href)
            unique_links.append(href)

    print(f"Found {len(unique_links)} unique potential menu links.")

    # Create data and temp directories
    data_dir = Path("data")
    temp_dir = data_dir / "temp"
    temp_dir.mkdir(exist_ok=True)

    found_menus = []
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

            # Check if this PDF is for any of the months we want
            for month in list(months_to_find):
                if is_pdf_for_month(temp_file, month):
                    # This is the correct menu, save it
                    output_file = data_dir / f"{month}.pdf"
                    temp_file.rename(output_file)
                    print(f"Successfully identified and saved {output_file}")
                    found_menus.append(output_file)
                    months_to_find.remove(month) # Don't need to find this month again
                    break

            if not months_to_find:
                print("Found all requested menus.")
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

    if not found_menus:
        print(f"\nCould not find any menus for {current_month} or {next_month}.")
        return False

    # On success, print the paths to the final files for the orchestrator
    for menu_path in found_menus:
        print(menu_path)
    return True


if __name__ == "__main__":
    success = download_menu()
    exit(0 if success else 1)