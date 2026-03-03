#!/usr/bin/env python3
"""Generate WhatsApp-ready reminder message for pending editing projects.

Reads from Google Sheets via sheets_sync and outputs a formatted message
suitable for copying into WhatsApp or capturing via iPhone Shortcut SSH.

Usage:
    python3 editor_reminder_summary.py              # All editors summary
    python3 editor_reminder_summary.py --editor Laxman  # Single editor
    python3 editor_reminder_summary.py --feedback    # Include pending corrections
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime

from sheets_sync import read_projects, read_video_projects, read_feedback


def get_pending(projects):
    """Filter to non-completed projects with days elapsed."""
    today = datetime.now()
    pending = []
    for p in projects:
        if "completed" in p["status"].lower():
            continue
        try:
            sent = datetime.strptime(p["date_sent"], "%Y-%m-%d")
            p["days_elapsed"] = (today - sent).days
        except (ValueError, KeyError):
            p["days_elapsed"] = 0
        pending.append(p)
    return pending


def build_message(editor_filter=None, include_feedback=False):
    """Build WhatsApp-ready reminder message."""
    # Gather pending projects
    photo_projects = get_pending(read_projects())
    video_projects = get_pending(read_video_projects())
    all_projects = photo_projects + video_projects

    # Group by editor
    by_editor = defaultdict(list)
    for p in all_projects:
        editor = p.get("editor", "Unknown")
        by_editor[editor].append(p)

    if editor_filter:
        # Case-insensitive match
        match = None
        for name in by_editor:
            if name.lower() == editor_filter.lower():
                match = name
                break
        if not match:
            return f"No pending projects for {editor_filter}."
        by_editor = {match: by_editor[match]}

    if not by_editor or all(len(v) == 0 for v in by_editor.values()):
        return "No pending projects right now."

    # Gather feedback corrections if requested
    corrections_by_project = defaultdict(list)
    if include_feedback:
        try:
            feedback = read_feedback()
            for entry in feedback:
                if entry["type"] == "correction" and not entry["fixed"]:
                    corrections_by_project[entry["project"].lower()].append(entry)
        except Exception:
            pass  # Feedback is optional

    # Build message
    lines = []
    for editor, projects in sorted(by_editor.items()):
        lines.append(f"Hi bro,\n")
        lines.append("Pending projects update:\n")

        for p in sorted(projects, key=lambda x: x.get("days_elapsed", 0), reverse=True):
            days = p.get("days_elapsed", 0)
            overdue = " (OVERDUE)" if days > p.get("expected_days", 14) else ""
            lines.append(f"  \u2022 {p['task']} \u2014 {days} days{overdue}")

            # Add unfixed corrections for this project
            proj_corrections = corrections_by_project.get(p["task"].lower(), [])
            for c in proj_corrections:
                ts = f"[{c['timestamp']}] " if c.get("timestamp") else ""
                lines.append(f"    \u2192 {ts}{c['content']}")

        lines.append("\nCould you share an update on these?\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Editor reminder summary")
    parser.add_argument("--editor", help="Filter to specific editor name")
    parser.add_argument("--feedback", action="store_true",
                        help="Include pending corrections from feedback sheet")
    args = parser.parse_args()

    msg = build_message(editor_filter=args.editor, include_feedback=args.feedback)
    print(msg)


if __name__ == "__main__":
    main()
