#!/usr/bin/env python3
"""
Shared Google Sheets helper for editing project tracking.

Reads/writes to the Google Sheet that Laxman uses to track editing status.
The Sheet is the single source of truth — scripts read from it and append to it.

Setup:
  1. Enable Google Sheets API in GCP console
  2. Create service account, download JSON key
  3. Save key to ~/.config/rsquare/sheets_credentials.json
  4. Share the Sheet with the service account email (Editor access)
  5. pip3 install gspread --break-system-packages
"""

import gspread
from pathlib import Path

SHEET_ID = "***REDACTED_SHEET_ID***"
CREDENTIALS_PATH = Path.home() / ".config" / "rsquare" / "sheets_credentials.json"

# Expected column headers (row 1 of the Sheet)
EXPECTED_HEADERS = ["Task", "Date Sent", "Priority", "Status", "Edit Completed", "Delivery Link"]


def get_sheet():
    """Authenticate and return the first worksheet of the editing tracker Sheet."""
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Google Sheets credentials not found at {CREDENTIALS_PATH}\n"
            "Follow setup instructions in sheets_sync.py to configure."
        )
    gc = gspread.service_account(filename=str(CREDENTIALS_PATH))
    spreadsheet = gc.open_by_key(SHEET_ID)
    return spreadsheet.sheet1


def _row_to_dict(headers, row):
    """Convert a Sheet row (list of values) to a project dict matching the JSON format."""
    # Pad row with empty strings if shorter than headers
    padded = row + [""] * (len(headers) - len(row))
    raw = dict(zip(headers, padded))

    return {
        "task": raw.get("Task", ""),
        "date_sent": raw.get("Date Sent", ""),
        "priority": raw.get("Priority", "P1"),
        "status": raw.get("Status", "SENT"),
        "edit_completed": raw.get("Edit Completed", "") or None,
        "delivery_link": raw.get("Delivery Link", ""),
        # Defaults not in Sheet — kept for compatibility with dashboard/reminder
        "editor": "Laxman",
        "editor_phone": "***REDACTED_PHONE***",
        "expected_days": 14,
    }


def read_projects():
    """Read all rows from the Sheet and return as a list of project dicts."""
    sheet = get_sheet()
    records = sheet.get_all_values()

    if not records:
        return []

    headers = records[0]
    projects = []
    for row in records[1:]:
        # Skip completely empty rows
        if not any(cell.strip() for cell in row):
            continue
        projects.append(_row_to_dict(headers, row))

    return projects


def add_project(data):
    """Append a new project row to the Sheet.

    Args:
        data: dict with keys matching the JSON format (task, date_sent, priority, etc.)
    """
    sheet = get_sheet()
    row = [
        data.get("task", ""),
        data.get("date_sent", ""),
        data.get("priority", "P1"),
        data.get("status", "SENT"),
        data.get("edit_completed", "") or "",
        data.get("delivery_link", ""),
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")


def get_pending():
    """Return all non-COMPLETED projects."""
    projects = read_projects()
    return [p for p in projects if p["status"] != "COMPLETED"]
