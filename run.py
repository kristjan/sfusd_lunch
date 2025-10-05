#!/usr/bin/env python3
"""
Orchestrator script for the SFUSD Lunch Menu project.

This script runs the full pipeline:
1. Downloads the latest menu PDF for the current month.
2. If a new PDF was downloaded, it parses it into a JSON file.
3. If parsing is successful, it adds the menu to a Home Assistant calendar.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def main():
    """Main orchestration function."""
    print("--- Starting SFUSD Lunch Menu Pipeline ---")

    # --- 1. Determine current state ---
    current_month = datetime.now().strftime("%B").lower()
    pdf_path = Path(f"data/{current_month}.pdf")
    pdf_existed = pdf_path.exists()

    print(f"Current month: {current_month}")
    if pdf_existed:
        print(f"PDF for {current_month} already exists. Running downloader to check for updates.")
    else:
        print(f"No PDF found for {current_month}. Attempting to download.")

    # --- 2. Run the download script ---
    print("\n[Step 1/3] Running download script...")
    try:
        # We use sys.executable to ensure we run with the same python interpreter
        result = subprocess.run(
            [sys.executable, "download.py"],
            capture_output=True, text=True, check=True, encoding='utf-8'
        )

        # The script will print the path of the downloaded file on the last line of its stdout
        output_lines = result.stdout.strip().splitlines()
        downloaded_pdf_path = output_lines[-1] if output_lines else ""

        if not downloaded_pdf_path or not Path(downloaded_pdf_path).exists():
            print("Downloader ran, but did not return a valid file path. Exiting.")
            # Also print stdout for debugging, in case the script printed something else
            print(f"Full output:\n{result.stdout}")
            sys.exit(0)

        print(f"Download script finished. Output path: {downloaded_pdf_path}")
        newly_downloaded = True # Assume if it prints a path, it's new/updated.
    except subprocess.CalledProcessError as e:
        print("❌ Download script failed.")
        print(f"   Exit Code: {e.returncode}")
        print(f"   Stderr: {e.stderr}")
        sys.exit(1)

    # --- 3. Run the parse script (only if needed) ---
    json_path = Path(downloaded_pdf_path).with_suffix('.json')

    if json_path.exists():
        print(f"\n[Step 2/3] Skipping parse: JSON file '{json_path}' already exists.")
        newly_parsed = False
    else:
        print("\n[Step 2/3] Running parse script...")
        try:
            result = subprocess.run(
                [sys.executable, "parse_menu.py", downloaded_pdf_path],
                capture_output=True, text=True, check=True, encoding='utf-8'
            )
            # The script will print the path of the JSON file on the last line
            output_lines = result.stdout.strip().splitlines()
            parsed_json_path = output_lines[-1] if output_lines else ""

            if not parsed_json_path or not Path(parsed_json_path).exists():
                 print("❌ Parse script ran but did not return a valid file path.")
                 print(f"Full output:\n{result.stdout}")
                 sys.exit(1)

            print(f"Parse script finished. Output path: {parsed_json_path}")
            newly_parsed = True

        except subprocess.CalledProcessError as e:
            print("❌ Parse script failed.")
            print(f"   Exit Code: {e.returncode}")
            print(f"   Stderr: {e.stderr}")
            sys.exit(1)

    # --- 4. Run the Home Assistant script (only if a new JSON was created) ---
    if newly_parsed:
        print("\n[Step 3/3] Running Home Assistant script...")
        try:
            subprocess.run(
                [sys.executable, "add_to_homeassistant.py", parsed_json_path],
                check=True, encoding='utf-8'
            )
            print("Home Assistant script finished.")

        except subprocess.CalledProcessError as e:
            print("❌ Home Assistant script failed.")
            print(f"   Exit Code: {e.returncode}")
            sys.exit(1)
    else:
        print("\n[Step 3/3] Skipping Home Assistant script (no new JSON data).")

    print("\n--- SFUSD Lunch Menu Pipeline Finished Successfully ---")

if __name__ == "__main__":
    main()
