#!/usr/bin/env python3
"""
Shared Google Sheets helper for editing project tracking.

Reads/writes to the Google Sheet that Laxman uses to track editing status.
The Sheet is the single source of truth — scripts read from it and append to it.

Read access uses public CSV export (no credentials needed — sheet is "anyone with link").
Write access (add_project) requires gspread + service account credentials.

Setup (only needed for write access):
  1. Enable Google Sheets API in GCP console
  2. Create service account, download JSON key
  3. Save key to ~/.config/rsquare/sheets_credentials.json
  4. Share the Sheet with the service account email (Editor access)
  5. pip3 install gspread --break-system-packages
"""

import csv
import io
import urllib.parse
import urllib.request
from pathlib import Path

SHEET_ID = "***REMOVED***"
CREDENTIALS_PATH = Path.home() / ".config" / "rsquare" / "sheets_credentials.json"

# GID for each tab (from the sheet URL ?gid=...)
GID_PROJECTS = "0"

# Tab 2: video editing projects (Madhu, GL Studios, Karthik)
GID_VIDEO_PROJECTS = "1513492429"

# Client reviews are in a separate Google Sheet (Rsquare_Review_Sheet)
# accessed via the same sheet ID but different tab — see CLAUDE.md
REVIEW_SHEET_ID = "***REMOVED***"


def _fetch_public_csv(sheet_id, gid):
    """Fetch a public Google Sheet tab as CSV and return list of rows."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    req = urllib.request.Request(url, headers={"User-Agent": "rsquare-sync/1.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    text = resp.read().decode("utf-8")
    reader = csv.reader(io.StringIO(text))
    return list(reader)


def get_sheet():
    """Authenticate and return the first worksheet (for write operations)."""
    import gspread
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Google Sheets credentials not found at {CREDENTIALS_PATH}\n"
            "Credentials are only needed for write operations (add_project)."
        )
    gc = gspread.service_account(filename=str(CREDENTIALS_PATH))
    spreadsheet = gc.open_by_key(SHEET_ID)
    return spreadsheet.sheet1


def _normalize_date(date_str):
    """Normalize date from M/D/YYYY (Google Sheets) to YYYY-MM-DD."""
    if not date_str or not date_str.strip():
        return ""
    date_str = date_str.strip()
    # Already in YYYY-MM-DD format
    if len(date_str) >= 8 and date_str[4] == "-":
        return date_str
    # M/D/YYYY or MM/DD/YYYY
    from datetime import datetime
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def _row_to_dict(headers, row):
    """Convert a Sheet row to a project dict. Matches headers generically."""
    padded = row + [""] * (len(headers) - len(row))
    raw = dict(zip(headers, padded))

    # Map actual sheet headers to internal keys (case-insensitive partial match)
    def find(keywords):
        for h in headers:
            hl = h.lower().strip()
            if all(k in hl for k in keywords):
                return raw.get(h, "")
        return ""

    return {
        "task": find(["task"]),
        "date_sent": _normalize_date(find(["sent"])),
        "priority": find(["priority"]) or "P1",
        "status": find(["status"]) or "SENT",
        "edit_completed": _normalize_date(find(["completed"])) or None,
        "delivery_link": find(["link"]) or find(["transfer"]),
        # Defaults not in Sheet — kept for compatibility with dashboard/reminder
        "editor": "Laxman",
        "editor_phone": "***REMOVED***",
        "expected_days": 14,
    }


def read_projects():
    """Read all rows from the Sheet and return as a list of project dicts."""
    records = _fetch_public_csv(SHEET_ID, GID_PROJECTS)

    if not records:
        return []

    headers = records[0]
    projects = []
    for row in records[1:]:
        if not any(cell.strip() for cell in row):
            continue
        proj = _row_to_dict(headers, row)
        # Skip rows with no task name or no date
        if not proj["task"].strip() or not proj["date_sent"]:
            continue
        projects.append(proj)

    return projects


def add_project(data):
    """Append a new project row to the Sheet (requires credentials)."""
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


def _video_row_to_dict(headers, row):
    """Convert a Sheet row to a video project dict. Like _row_to_dict but with editor column."""
    padded = row + [""] * (len(headers) - len(row))
    raw = dict(zip(headers, padded))

    def find(keywords):
        for h in headers:
            hl = h.lower().strip()
            if all(k in hl for k in keywords):
                return raw.get(h, "")
        return ""

    return {
        "task": find(["task"]),
        "date_sent": _normalize_date(find(["sent"])),
        "editor": find(["editor"]) or "Madhu",
        "priority": find(["priority"]) or "P1",
        "status": find(["status"]) or "SENT",
        "edit_completed": _normalize_date(find(["completed"])) or None,
        "delivery_link": find(["link"]) or find(["transfer"]),
        "expected_days": 14,
    }


def read_video_projects():
    """Read video editing projects from tab 2 of the Sheet."""
    records = _fetch_public_csv(SHEET_ID, GID_VIDEO_PROJECTS)

    if not records:
        return []

    headers = records[0]
    projects = []
    for row in records[1:]:
        if not any(cell.strip() for cell in row):
            continue
        proj = _video_row_to_dict(headers, row)
        if not proj["task"].strip() or not proj["date_sent"]:
            continue
        projects.append(proj)

    return projects


VIDEO_PROJECT_SCRIPT_URL = "https://script.google.com/macros/s/***REMOVED***/exec"


def add_video_project(data):
    """Append a new video project row to tab 2 via Google Apps Script."""
    params = urllib.parse.urlencode({
        "type": "video_project",
        "task": data.get("task", ""),
        "date_sent": data.get("date_sent", ""),
        "editor": data.get("editor", "Madhu"),
        "priority": data.get("priority", "P1"),
        "status": data.get("status", "SENT"),
        "edit_completed": data.get("edit_completed", "") or "",
        "delivery_link": data.get("delivery_link", ""),
    }).encode("utf-8")
    req = urllib.request.Request(VIDEO_PROJECT_SCRIPT_URL, data=params, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    resp = urllib.request.urlopen(req, timeout=15)
    return resp.read().decode("utf-8")


# GID for Feedback tab — update after creating the tab in Google Sheets
GID_FEEDBACK = "***REMOVED***"


def read_feedback(project=None):
    """Read feedback entries from the 'Feedback' tab.

    Args:
        project: Optional project name to filter by. If None, returns all.

    Returns list of dicts: {project, type, timestamp, content, priority, submitted}
    """
    if not GID_FEEDBACK:
        return []

    records = _fetch_public_csv(SHEET_ID, GID_FEEDBACK)

    if not records or len(records) < 2:
        return []

    headers = records[0]
    entries = []
    for row in records[1:]:
        if not any(cell.strip() for cell in row):
            continue
        padded = row + [""] * (len(headers) - len(row))
        raw = dict(zip(headers, padded))
        entry = {
            "project": raw.get("Project", "").strip(),
            "type": raw.get("Type", "").strip(),
            "timestamp": raw.get("Timestamp", "").strip(),
            "content": raw.get("Content", "").strip(),
            "priority": raw.get("Priority", "").strip(),
            "submitted": raw.get("Submitted", "").strip(),
            "fixed": raw.get("Fixed", "").strip().lower() == "yes",
        }
        if project and entry["project"].lower() != project.lower():
            continue
        entries.append(entry)

    return entries


def get_project_feedback_url(project_slug):
    """Return the feedback URL for a project."""
    return f"https://portfolio.rsquarestudios.com/feedback/?p={project_slug}"


def read_reviews():
    """Read approved reviews from the 'Reviews' tab.

    Returns list of dicts: {name, event_type, rating, review, date}
    Only returns rows where Status == 'approved'.
    """
    records = _fetch_public_csv(REVIEW_SHEET_ID, GID_VIDEO_PROJECTS)

    if not records or len(records) < 2:
        return []

    headers = records[0]
    reviews = []
    for row in records[1:]:
        if not any(cell.strip() for cell in row):
            continue
        padded = row + [""] * (len(headers) - len(row))
        raw = dict(zip(headers, padded))
        if raw.get("Status", "").strip().lower() != "approved":
            continue
        reviews.append({
            "name": raw.get("Name", "").strip(),
            "event_type": raw.get("Event Type", "").strip(),
            "rating": int(raw.get("Rating", "5") or "5"),
            "review": raw.get("Review", "").strip(),
            "date": raw.get("Date", "").strip(),
        })

    return reviews
