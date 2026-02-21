#!/usr/bin/env python3
"""Daily editing project reminder — shows osascript popup for overdue projects."""

import json
import subprocess
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECTS_FILE = SCRIPT_DIR / "editing_projects.json"


def load_projects():
    with open(PROJECTS_FILE) as f:
        return json.load(f)["projects"]


def get_overdue_projects(projects):
    today = datetime.now()
    overdue = []
    for p in projects:
        if p["status"] == "COMPLETED":
            continue
        sent = datetime.strptime(p["date_sent"], "%Y-%m-%d")
        days_elapsed = (today - sent).days
        if days_elapsed > p["expected_days"]:
            p["days_elapsed"] = days_elapsed
            overdue.append(p)
    return overdue


def build_wa_link(project):
    """Generate wa.me deep link with pre-filled follow-up message."""
    phone = project.get("editor_phone", "")
    if not phone:
        return None

    sent_date = datetime.strptime(project["date_sent"], "%Y-%m-%d").strftime("%b %d")
    editor = project.get("editor", "there")
    msg = (
        f"Hi {editor},\n\n"
        f"Just checking in on the {project['task']} edit — "
        f"it's been {project['days_elapsed']} days since I sent the files on {sent_date}.\n\n"
        f"Could you share an update on the progress? "
        f"Let me know if you need anything!\n\n"
        f"Thanks,\nRam"
    )
    encoded = urllib.parse.quote(msg)
    return f"https://wa.me/{phone}?text={encoded}"


def show_popup(overdue):
    """Show osascript popup listing overdue projects."""
    lines = []
    for p in overdue:
        priority = p["priority"]
        lines.append(f"• {p['task']} ({priority}) — {p['days_elapsed']} days waiting")

    body = "\\n".join(lines)
    count = len(overdue)
    title = f"Editing Projects — {count} Overdue"

    # Build osascript command
    script = (
        f'display dialog "{count} overdue editing project(s):\\n\\n{body}" '
        f'with title "{title}" '
        f'buttons {{"Dismiss", "Follow Up"}} default button 2 '
        f'with icon caution'
    )

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=300
        )
        output = result.stdout.strip()
        if "Follow Up" in output:
            open_follow_ups(overdue)
    except subprocess.TimeoutExpired:
        pass


def open_follow_ups(overdue):
    """Open wa.me links for overdue projects that have editor phone numbers."""
    opened = 0
    no_phone = []

    for p in overdue:
        link = build_wa_link(p)
        if link:
            webbrowser.open(link)
            opened += 1
        else:
            no_phone.append(p["task"])

    if no_phone:
        # Show which projects are missing editor phone numbers
        missing = ", ".join(no_phone)
        script = (
            f'display dialog "No phone number for: {missing}\\n\\n'
            f'Add editor_phone in editing_projects.json to enable WhatsApp follow-up." '
            f'with title "Missing Editor Contacts" '
            f'buttons {{"OK"}} default button 1 with icon note'
        )
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=30)


def get_pending_projects(projects):
    """Get all non-completed projects with days elapsed."""
    today = datetime.now()
    pending = []
    for p in projects:
        if p["status"] == "COMPLETED":
            continue
        sent = datetime.strptime(p["date_sent"], "%Y-%m-%d")
        p["days_elapsed"] = (today - sent).days
        pending.append(p)
    return pending


def build_pending_summary_link(pending):
    """Generate wa.me link with a summary of all pending projects."""
    if not pending:
        return None

    phone = pending[0].get("editor_phone", "")
    editor = pending[0].get("editor", "there")
    if not phone:
        return None

    lines = []
    for p in pending:
        sent_date = datetime.strptime(p["date_sent"], "%Y-%m-%d").strftime("%b %d")
        status = "OVERDUE" if p["days_elapsed"] > p["expected_days"] else f"{p['days_elapsed']}d"
        lines.append(f"• {p['task']} ({p['priority']}) — sent {sent_date} [{status}]")

    project_list = "\n".join(lines)
    msg = (
        f"Hi {editor},\n\n"
        f"Here's a summary of the pending edits:\n\n"
        f"{project_list}\n\n"
        f"Could you share an update on these? "
        f"Let me know if you need anything!\n\n"
        f"Thanks,\nRam"
    )
    encoded = urllib.parse.quote(msg)
    return f"https://wa.me/{phone}?text={encoded}"


def show_pending_popup(pending):
    """Show popup with all pending projects and option to send WhatsApp summary."""
    lines = []
    for p in pending:
        status = "OVERDUE" if p["days_elapsed"] > p["expected_days"] else f"{p['days_elapsed']}d"
        lines.append(f"• {p['task']} ({p['priority']}) — {status}")

    body = "\\n".join(lines)
    count = len(pending)
    title = f"Pending Edits — {count} Projects"

    script = (
        f'display dialog "{count} pending editing project(s):\\n\\n{body}" '
        f'with title "{title}" '
        f'buttons {{"Dismiss", "Send to Laxman"}} default button 2 '
        f'with icon note'
    )

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=300
        )
        output = result.stdout.strip()
        if "Send to Laxman" in output:
            link = build_pending_summary_link(pending)
            if link:
                webbrowser.open(link)
    except subprocess.TimeoutExpired:
        pass


def main():
    projects = load_projects()

    # Check for --pending flag to send full summary
    import sys
    if "--pending" in sys.argv:
        pending = get_pending_projects(projects)
        if not pending:
            print("No pending projects.")
            return
        show_pending_popup(pending)
        return

    # Default: overdue-only reminder
    overdue = get_overdue_projects(projects)

    if not overdue:
        # Silent — no popup if nothing is overdue
        return

    show_popup(overdue)


if __name__ == "__main__":
    main()
