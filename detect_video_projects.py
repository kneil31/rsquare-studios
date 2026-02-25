#!/usr/bin/env python3
"""
Detect new video editing projects from SSD shoots or MEGA folders.

Cross-references against Google Sheet tab 2 (video editing projects) and
shows macOS popups for approval before adding new entries.
Can also upload Videos/ from SSD to MEGA before adding to Sheet.

Usage:
    python3 detect_video_projects.py --scan-ssd      # Scan SSD for shoots with Videos/
    python3 detect_video_projects.py --mega           # List MEGA folders, detect untracked
    python3 detect_video_projects.py --mega-url URL   # Add specific MEGA URL directly
        [--project-name NAME]                         # Optional project name override
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sheets_sync import read_video_projects, add_video_project

SCRIPT_DIR = Path(__file__).parent
GENERATOR = SCRIPT_DIR / "generate_dashboard.py"

SSD_BASE = Path("/Volumes/CLIENT 2026/2026")
MEGA_FOLDER_URL = "https://***REMOVED***"
MEGA_VIDEO_PATH = "/Root/Video RAW Data/"

# Shoot folder pattern: YYYY-MM-DD | Name | Location
SHOOT_FOLDER_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|\s*(.+)$")

DEFAULTS = {
    "editor": "Madhu",
    "priority": "P1",
    "status": "SENT",
    "edit_completed": None,
    "delivery_link": "",
}


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
            return None
        return result.stdout.strip().split(":")[-1]
    except subprocess.TimeoutExpired:
        return None


def is_tracked(name, tracked_tasks):
    """Check if a shoot name matches any existing video project task."""
    name_lower = name.lower()
    for task in tracked_tasks:
        task_lower = task.lower()
        if name_lower in task_lower or task_lower in name_lower:
            return True
    return False


def upload_to_mega(project_name, videos_dir):
    """Upload MP4s from a local Videos/ dir to MEGA. Returns True on success."""
    remote_folder = f"{MEGA_VIDEO_PATH}{project_name} Videos"

    # Create remote folder
    print(f"  Creating MEGA folder: {remote_folder}")
    result = subprocess.run(
        ["megatools", "mkdir", remote_folder],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Folder already exists is OK
        if "already exists" not in stderr.lower():
            print(f"  Error creating MEGA folder: {stderr}")
            return False

    # Collect MP4 files (skip macOS ._ resource forks)
    mp4s = sorted(
        p for p in videos_dir.iterdir()
        if p.suffix.lower() == ".mp4" and not p.name.startswith("._")
    )

    if not mp4s:
        print("  No MP4 files to upload.")
        return False

    total = len(mp4s)
    print(f"  Uploading {total} MP4(s) to {remote_folder}...")

    failed = []
    for i, mp4 in enumerate(mp4s, 1):
        print(f"  [{i}/{total}] {mp4.name} ({mp4.stat().st_size / (1024*1024):.0f} MB)")
        result = subprocess.run(
            ["megatools", "put", "--path", remote_folder, str(mp4)],
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "already exists" in stderr.lower():
                print(f"    Already exists, skipping.")
            else:
                print(f"    Upload failed: {stderr}")
                failed.append(mp4.name)

    if failed:
        print(f"  {len(failed)} file(s) failed to upload: {', '.join(failed)}")
        return len(failed) < total  # Partial success if some uploaded
    else:
        print(f"  All {total} MP4(s) uploaded successfully.")
        return True


def scan_ssd():
    """Scan SSD for shoot folders with a Videos/ subfolder containing MP4s."""
    if not SSD_BASE.exists():
        print(f"Error: SSD not mounted at {SSD_BASE}")
        osascript_dialog(
            "Video Detector",
            f"SSD not mounted at:\\n{SSD_BASE}",
            buttons=("OK",),
            icon="stop",
        )
        sys.exit(1)

    candidates = []
    for folder in sorted(SSD_BASE.iterdir()):
        if not folder.is_dir():
            continue
        match = SHOOT_FOLDER_RE.match(folder.name)
        if not match:
            continue

        videos_dir = folder / "Videos"
        if not videos_dir.is_dir():
            continue

        # Count MP4s, excluding macOS ._ resource fork files
        mp4s = [
            p for p in videos_dir.iterdir()
            if p.suffix.lower() == ".mp4" and not p.name.startswith("._")
        ]
        if not mp4s:
            continue

        date_str, name, location = match.groups()
        candidates.append({
            "folder_name": folder.name,
            "date": date_str,
            "name": name.strip(),
            "location": location.strip(),
            "mp4_count": len(mp4s),
            "path": str(folder),
            "videos_dir": str(videos_dir),
        })

    return candidates


def scan_mega():
    """List MEGA folders and return as candidates."""
    print(f"Listing MEGA folders in {MEGA_VIDEO_PATH}...")
    try:
        result = subprocess.run(
            ["megatools", "ls", MEGA_VIDEO_PATH],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        print("Error: megatools not installed. Install with: brew install megatools")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Error: megatools timed out (check ~/.megarc credentials)")
        sys.exit(1)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "No such file or directory" in stderr or "not found" in stderr.lower():
            print("Error: ~/.megarc not found. Create it with MEGA credentials:")
            print("  [Login]")
            print("  Username = your@email.com")
            print("  Password = your_password")
        else:
            print(f"Error listing MEGA: {stderr}")
        sys.exit(1)

    candidates = []
    parent = MEGA_VIDEO_PATH.rstrip("/").split("/")[-1]
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # megatools ls output: /Root/Video RAW Data/FolderName
        folder_name = line.split("/")[-1]
        if not folder_name or folder_name == parent:
            continue
        candidates.append({
            "name": folder_name,
            "mega_path": line,
            "delivery_link": MEGA_FOLDER_URL,
        })

    return candidates


def add_mega_url(url, project_name=None):
    """Add a specific MEGA URL as a video project."""
    if not url.startswith("https://mega.nz/"):
        print(f"Error: Invalid MEGA URL: {url}")
        sys.exit(1)

    if not project_name:
        project_name = input("Project name: ").strip()
        if not project_name:
            print("Error: Project name required.")
            sys.exit(1)

    today = datetime.now().strftime("%Y-%m-%d")
    entry = {
        "task": project_name,
        "date_sent": today,
        "delivery_link": url,
        **DEFAULTS,
    }

    print(f"Adding: {project_name} → {url}")
    add_video_project(entry)
    print("Added to Google Sheet (tab 2).")

    regenerate_dashboard()


def show_ssd_candidates_and_add(candidates):
    """Show SSD candidates with option to upload to MEGA first."""
    # Get existing video projects from Sheet
    print("Reading video projects from Google Sheet...")
    existing = read_video_projects()
    tracked_tasks = [p["task"] for p in existing]
    print(f"Video projects: {len(tracked_tasks)} tracked")

    # Filter to untracked
    untracked = [c for c in candidates if not is_tracked(c["name"], tracked_tasks)]

    if not untracked:
        print("No untracked video projects found on SSD.")
        osascript_dialog(
            "Video Detector",
            "No untracked video projects found.\\nAll SSD shoots are already tracked.",
            buttons=("OK",),
        )
        return

    print(f"\nFound {len(untracked)} untracked video project(s):")
    for c in untracked:
        print(f"  • {c['name']} ({c['mp4_count']} MP4s)")

    # Summary popup
    summary_lines = [f"{len(untracked)} untracked video project(s) on SSD:\\n"]
    for c in untracked:
        summary_lines.append(f"• {c['name']} ({c['mp4_count']} MP4s)")
    summary_msg = "\\n".join(summary_lines)

    action = osascript_dialog(
        "Video Detector",
        summary_msg,
        buttons=("Dismiss", "Review"),
        default_button="Review",
    )

    if action != "Review":
        print("Dismissed.")
        return

    # Per-project confirmation with upload option
    added = []
    today = datetime.now().strftime("%Y-%m-%d")

    for c in untracked:
        msg = (
            f"Add \\\"{c['name']}\\\" to video editing tracker?\\n\\n"
            f"MP4 files: {c['mp4_count']}\\n"
            f"Location: {c['location']}\\n"
            f"Editor: {DEFAULTS['editor']} | Priority: {DEFAULTS['priority']}\\n\\n"
            f"Upload & Add = upload to MEGA first, then add to Sheet\\n"
            f"Add Only = add to Sheet without uploading"
        )
        choice = osascript_dialog(
            f"Video Project — {c['name']}",
            msg,
            buttons=("Skip", "Add Only", "Upload & Add"),
            default_button="Upload & Add",
        )

        if choice == "Upload & Add":
            print(f"\n  Uploading {c['name']} to MEGA...")
            success = upload_to_mega(c["name"], Path(c["videos_dir"]))
            link = MEGA_FOLDER_URL if success else ""
            entry = {
                "task": c["name"],
                "date_sent": c.get("date", today),
                "delivery_link": link,
                **DEFAULTS,
            }
            added.append(entry)
            status = "uploaded + added" if success else "added (upload had errors)"
            print(f"  ✓ {c['name']}: {status}")

        elif choice == "Add Only":
            entry = {
                "task": c["name"],
                "date_sent": c.get("date", today),
                **DEFAULTS,
            }
            added.append(entry)
            print(f"  ✓ Added: {c['name']} (no upload)")

        else:
            print(f"  ✗ Skipped: {c['name']}")

    if not added:
        print("\nNo projects added.")
        return

    # Append to Google Sheet
    for entry in added:
        add_video_project(entry)
    print(f"\nAppended {len(added)} video project(s) to Google Sheet (tab 2)")

    regenerate_dashboard()

    # Final confirmation
    names = ", ".join(e["task"] for e in added)
    osascript_dialog(
        "Video Detector",
        f"Added {len(added)} video project(s):\\n{names}\\n\\nDashboard regenerated.",
        buttons=("OK",),
    )


def show_mega_candidates_and_add(candidates):
    """Show MEGA candidates and add approved ones to Sheet."""
    print("Reading video projects from Google Sheet...")
    existing = read_video_projects()
    tracked_tasks = [p["task"] for p in existing]
    print(f"Video projects: {len(tracked_tasks)} tracked")

    untracked = [c for c in candidates if not is_tracked(c["name"], tracked_tasks)]

    if not untracked:
        print("No untracked video projects found in MEGA.")
        osascript_dialog(
            "Video Detector",
            "No untracked video projects found.\\nAll MEGA folders are already tracked.",
            buttons=("OK",),
        )
        return

    print(f"\nFound {len(untracked)} untracked video project(s):")
    for c in untracked:
        print(f"  • {c['name']}")

    summary_lines = [f"{len(untracked)} untracked video project(s) in MEGA:\\n"]
    for c in untracked:
        summary_lines.append(f"• {c['name']}")
    summary_msg = "\\n".join(summary_lines)

    action = osascript_dialog(
        "Video Detector",
        summary_msg,
        buttons=("Dismiss", "Review"),
        default_button="Review",
    )

    if action != "Review":
        print("Dismissed.")
        return

    added = []
    today = datetime.now().strftime("%Y-%m-%d")

    for c in untracked:
        msg = (
            f"Add \\\"{c['name']}\\\" to video editing tracker?\\n\\n"
            f"MEGA path: {c['mega_path']}\\n"
            f"Editor: {DEFAULTS['editor']} | Priority: {DEFAULTS['priority']}"
        )
        choice = osascript_dialog(
            f"Add Video Project — {c['name']}",
            msg,
            buttons=("Skip", "Add"),
            default_button="Add",
        )

        if choice == "Add":
            entry = {
                "task": c["name"],
                "date_sent": today,
                "delivery_link": c.get("delivery_link", MEGA_FOLDER_URL),
                **DEFAULTS,
            }
            added.append(entry)
            print(f"  ✓ Added: {c['name']}")
        else:
            print(f"  ✗ Skipped: {c['name']}")

    if not added:
        print("\nNo projects added.")
        return

    for entry in added:
        add_video_project(entry)
    print(f"\nAppended {len(added)} video project(s) to Google Sheet (tab 2)")

    regenerate_dashboard()

    names = ", ".join(e["task"] for e in added)
    osascript_dialog(
        "Video Detector",
        f"Added {len(added)} video project(s):\\n{names}\\n\\nDashboard regenerated.",
        buttons=("OK",),
    )


def auto_ssd(candidates):
    """Auto mode: upload all untracked SSD shoots to MEGA and add to Sheet. No popups."""
    print("Reading video projects from Google Sheet...")
    existing = read_video_projects()
    tracked_tasks = [p["task"] for p in existing]
    print(f"Video projects: {len(tracked_tasks)} tracked")

    untracked = [c for c in candidates if not is_tracked(c["name"], tracked_tasks)]

    if not untracked:
        print("No untracked video projects found on SSD.")
        return

    print(f"\n{len(untracked)} untracked video project(s) — auto uploading & adding:")
    added = []
    today = datetime.now().strftime("%Y-%m-%d")

    for c in untracked:
        print(f"\n  Uploading {c['name']} ({c['mp4_count']} MP4s) to MEGA...")
        success = upload_to_mega(c["name"], Path(c["videos_dir"]))
        link = MEGA_FOLDER_URL if success else ""
        entry = {
            "task": c["name"],
            "date_sent": c.get("date", today),
            "delivery_link": link,
            **DEFAULTS,
        }
        add_video_project(entry)
        added.append(entry)
        status = "uploaded + added" if success else "added (upload had errors)"
        print(f"  ✓ {c['name']}: {status}")

    print(f"\nAuto-added {len(added)} video project(s) to Google Sheet (tab 2)")
    regenerate_dashboard()


def auto_mega(candidates):
    """Auto mode: add all untracked MEGA folders to Sheet. No popups."""
    print("Reading video projects from Google Sheet...")
    existing = read_video_projects()
    tracked_tasks = [p["task"] for p in existing]
    print(f"Video projects: {len(tracked_tasks)} tracked")

    untracked = [c for c in candidates if not is_tracked(c["name"], tracked_tasks)]

    if not untracked:
        print("No untracked video projects found in MEGA.")
        return

    print(f"\n{len(untracked)} untracked video project(s) — auto adding:")
    added = []
    today = datetime.now().strftime("%Y-%m-%d")

    for c in untracked:
        entry = {
            "task": c["name"],
            "date_sent": today,
            "delivery_link": c.get("delivery_link", MEGA_FOLDER_URL),
            **DEFAULTS,
        }
        add_video_project(entry)
        added.append(entry)
        print(f"  ✓ Added: {c['name']}")

    print(f"\nAuto-added {len(added)} video project(s) to Google Sheet (tab 2)")
    regenerate_dashboard()


def regenerate_dashboard():
    """Regenerate the dashboard HTML."""
    print("Regenerating dashboard...")
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("Dashboard regenerated successfully.")
    else:
        print(f"Dashboard generation failed:\n{result.stderr}")


def main():
    parser = argparse.ArgumentParser(
        description="Detect new video editing projects from SSD or MEGA"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan-ssd", action="store_true",
                       help="Scan SSD for shoots with Videos/ subfolder")
    group.add_argument("--mega", action="store_true",
                       help="List MEGA folders, detect untracked")
    group.add_argument("--mega-url", type=str,
                       help="Add a specific MEGA URL directly")
    parser.add_argument("--project-name", type=str,
                        help="Project name (for --mega-url mode)")
    parser.add_argument("--auto", action="store_true",
                        help="Auto mode: skip popups, upload & add all untracked (for LaunchAgent)")

    args = parser.parse_args()

    if args.scan_ssd:
        candidates = scan_ssd()
        if not candidates:
            print("No shoot folders with Videos/ found on SSD.")
            if not args.auto:
                osascript_dialog(
                    "Video Detector",
                    "No shoot folders with Videos/ subfolder found on SSD.",
                    buttons=("OK",),
                )
            return
        print(f"Found {len(candidates)} shoot(s) with Videos/ on SSD")
        if args.auto:
            auto_ssd(candidates)
        else:
            show_ssd_candidates_and_add(candidates)

    elif args.mega:
        candidates = scan_mega()
        if not candidates:
            print("No folders found in MEGA.")
            return
        print(f"Found {len(candidates)} folder(s) in MEGA")
        if args.auto:
            auto_mega(candidates)
        else:
            show_mega_candidates_and_add(candidates)

    elif args.mega_url:
        add_mega_url(args.mega_url, args.project_name)


if __name__ == "__main__":
    main()
