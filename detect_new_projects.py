#!/usr/bin/env python3
"""
Detect new editing projects by cross-referencing Lightroom catalog index
against editing_projects.json. Shows untracked shoots via macOS popup.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CATALOG_INDEX = SCRIPT_DIR / ".." / "lrcat_indexer" / "catalog_index.json"
EDITING_PROJECTS = SCRIPT_DIR / "editing_projects.json"
GENERATOR = SCRIPT_DIR / "generate_dashboard.py"

LOOKBACK_DAYS = 60

# Defaults for new editing project entries
DEFAULTS = {
    "editor": "Laxman",
    "editor_phone": "919700453062",
    "priority": "P1",
    "status": "SENT",
    "edit_completed": None,
    "delivery_link": "",
    "expected_days": 14,
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_editing_projects(data):
    with open(EDITING_PROJECTS, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def osascript_dialog(title, message, buttons=("OK",), default_button=None, icon="note"):
    """Show a macOS dialog via osascript. Returns the button pressed."""
    btn_list = ", ".join(f'"{b}"' for b in buttons)
    default = default_button or buttons[-1]
    script = (
        f'display dialog "{message}" '
        f'with title "{title}" '
        f'buttons {{{btn_list}}} '
        f'default button "{default}" '
        f'with icon {icon}'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return None  # User cancelled or dismissed
        # Output like "button returned:Review"
        return result.stdout.strip().split(":")[-1]
    except subprocess.TimeoutExpired:
        return None


def get_recent_catalogs(catalog_data, cutoff_date):
    """Filter catalogs to those with recent activity."""
    recent = []
    for cat in catalog_data.get("catalogs", []):
        latest = cat.get("latest_date")
        modified = cat.get("modified")

        is_recent = False
        if latest:
            try:
                if datetime.strptime(latest, "%Y-%m-%d").date() >= cutoff_date:
                    is_recent = True
            except ValueError:
                pass
        if not is_recent and modified:
            try:
                mod_date = datetime.fromisoformat(modified).date()
                if mod_date >= cutoff_date:
                    is_recent = True
            except ValueError:
                pass

        if is_recent:
            recent.append(cat)
    return recent


def is_tracked(catalog_name, tracked_tasks):
    """Check if a catalog name matches any existing editing project task."""
    cat_lower = catalog_name.lower()
    for task in tracked_tasks:
        task_lower = task.lower()
        # Substring match in either direction
        if cat_lower in task_lower or task_lower in cat_lower:
            return True
    return False


def format_date(date_str):
    """Format a date string like 'Feb 11'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d").replace(" 0", " ")
    except (ValueError, TypeError):
        return date_str or "unknown"


def main():
    # Validate paths
    if not CATALOG_INDEX.exists():
        print(f"Error: catalog_index.json not found at {CATALOG_INDEX}")
        print("Run 'lrcat scan' first to build the index.")
        sys.exit(1)

    if not EDITING_PROJECTS.exists():
        print(f"Error: editing_projects.json not found at {EDITING_PROJECTS}")
        sys.exit(1)

    # Load data
    catalog_data = load_json(CATALOG_INDEX)
    editing_data = load_json(EDITING_PROJECTS)

    last_scan = catalog_data.get("last_scan", "unknown")
    print(f"Catalog index: {catalog_data.get('catalog_count', '?')} catalogs (last scan: {last_scan})")

    # Get tracked task names
    tracked_tasks = [p["task"] for p in editing_data.get("projects", [])]
    print(f"Editing projects: {len(tracked_tasks)} tracked")

    # Filter recent catalogs
    cutoff = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).date()
    recent = get_recent_catalogs(catalog_data, cutoff)
    print(f"Recent catalogs (last {LOOKBACK_DAYS} days): {len(recent)}")

    # Deduplicate by name (keep the one with the most photos — likely the latest version)
    by_name = {}
    for cat in recent:
        name = cat["name"]
        if name not in by_name or cat.get("photo_count", 0) > by_name[name].get("photo_count", 0):
            by_name[name] = cat
    recent = list(by_name.values())

    # Find untracked
    candidates = []
    for cat in recent:
        if not is_tracked(cat["name"], tracked_tasks):
            candidates.append(cat)

    if not candidates:
        print("No untracked shoots found. Everything is tracked!")
        osascript_dialog(
            "Editing Detector",
            "No untracked shoots found.\\nAll recent catalogs are already tracked.",
            buttons=("OK",),
        )
        return

    # Sort by latest_date descending
    candidates.sort(
        key=lambda c: c.get("latest_date") or c.get("modified", ""),
        reverse=True,
    )

    print(f"\nFound {len(candidates)} untracked shoots:")
    for c in candidates:
        print(f"  • {c['name']} ({c.get('photo_count', '?')} photos, {format_date(c.get('latest_date'))})")

    # Step 1: Summary popup
    summary_lines = [f"{len(candidates)} untracked shoot(s) found:\\n"]
    for c in candidates:
        date_str = format_date(c.get("latest_date"))
        summary_lines.append(
            f"• {c['name']} ({c.get('photo_count', '?')} photos, {date_str})"
        )
    summary_msg = "\\n".join(summary_lines)

    action = osascript_dialog(
        "Editing Detector",
        summary_msg,
        buttons=("Dismiss", "Review"),
        default_button="Review",
    )

    if action != "Review":
        print("Dismissed.")
        return

    # Step 2: Per-project confirmation
    added = []
    today = datetime.now().strftime("%Y-%m-%d")

    for c in candidates:
        date_str = format_date(c.get("latest_date"))
        msg = (
            f"Add \\\"{c['name']}\\\" to editing tracker?\\n\\n"
            f"Photos: {c.get('photo_count', '?')} | Shot: {date_str}\\n"
            f"Editor: {DEFAULTS['editor']} | Priority: {DEFAULTS['priority']}"
        )
        choice = osascript_dialog(
            f"Add Project — {c['name']}",
            msg,
            buttons=("Skip", "Add"),
            default_button="Add",
        )

        if choice == "Add":
            entry = {
                "task": c["name"],
                "date_sent": today,
                **DEFAULTS,
            }
            added.append(entry)
            print(f"  ✓ Added: {c['name']}")
        else:
            print(f"  ✗ Skipped: {c['name']}")

    if not added:
        print("\nNo projects added.")
        return

    # Append to editing_projects.json
    editing_data["projects"].extend(added)
    save_editing_projects(editing_data)
    print(f"\nAppended {len(added)} project(s) to editing_projects.json")

    # Regenerate dashboard
    print("Regenerating dashboard...")
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("Dashboard regenerated successfully.")
    else:
        print(f"Dashboard generation failed:\n{result.stderr}")

    # Final confirmation
    names = ", ".join(e["task"] for e in added)
    osascript_dialog(
        "Editing Detector",
        f"Added {len(added)} project(s):\\n{names}\\n\\nDashboard regenerated.",
        buttons=("OK",),
    )


if __name__ == "__main__":
    main()
