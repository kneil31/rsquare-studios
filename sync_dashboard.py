#!/usr/bin/env python3
"""
Daily dashboard sync — regenerates from Google Sheets and deploys if changed.

Reads editing projects + reviews from Google Sheets, regenerates index.html,
and pushes to GitHub Pages only if content changed.

Usage:
    python3 sync_dashboard.py           # Sync + deploy if changed
    python3 sync_dashboard.py --force   # Regenerate + deploy even if unchanged
    python3 sync_dashboard.py --dry-run # Regenerate but don't push

Designed to run daily via LaunchAgent (com.rsquare.dashboard-sync.plist).
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
GENERATE_SCRIPT = SCRIPT_DIR / "generate_dashboard.py"


def regenerate():
    """Run generate_dashboard.py to rebuild index.html."""
    result = subprocess.run(
        ["/opt/homebrew/bin/python3", str(GENERATE_SCRIPT)],
        capture_output=True, text=True, cwd=str(SCRIPT_DIR)
    )
    if result.returncode != 0:
        print(f"ERROR: Dashboard generation failed:\n{result.stderr}")
        sys.exit(1)
    print(result.stdout.rstrip())


def has_changes():
    """Check if index.html has uncommitted changes."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "index.html"],
        capture_output=True, text=True, cwd=str(SCRIPT_DIR)
    )
    return "index.html" in result.stdout


def deploy():
    """Commit and push index.html to GitHub Pages."""
    timestamp = datetime.now().strftime("%b %d %I:%M %p")
    subprocess.run(
        ["git", "add", "index.html"],
        cwd=str(SCRIPT_DIR), capture_output=True
    )
    result = subprocess.run(
        ["git", "commit", "-m", f"Daily sync: editing projects + reviews ({timestamp})"],
        cwd=str(SCRIPT_DIR), capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"WARNING: git commit failed:\n{result.stderr}")
        return False

    result = subprocess.run(
        ["git", "push"],
        cwd=str(SCRIPT_DIR), capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"WARNING: git push failed:\n{result.stderr}")
        return False

    print(f"  Pushed to GitHub Pages.")
    return True


def main():
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n--- Dashboard sync: {now} ---")

    # Regenerate
    print("Regenerating dashboard...")
    regenerate()

    # Check for changes
    changed = has_changes()
    if changed:
        print("  Changes detected in index.html.")
    else:
        print("  No changes detected.")

    # Deploy
    if dry_run:
        print("  Dry run — skipping push.")
    elif changed or force:
        deploy()
    else:
        print("  Nothing to deploy.")

    print("Done.\n")


if __name__ == "__main__":
    main()
