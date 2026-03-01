#!/usr/bin/env python3
"""Generate a 48-hour auto-unlock link for the Rsquare Studios dashboard."""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
SECRET_FILE = SCRIPT_DIR / ".secret"
BASE_URL = "https://portfolio.rsquarestudios.com/"


def main():
    if not SECRET_FILE.exists():
        print("ERROR: .secret file not found.")
        sys.exit(1)

    secrets = json.loads(SECRET_FILE.read_text())
    ts = int(time.time())
    expires = datetime.now() + timedelta(hours=48)

    link_type = sys.argv[1] if len(sys.argv) > 1 else "client"

    if link_type == "internal":
        pw = secrets["internal"]
    else:
        pw = secrets["client"]

    url = f"{BASE_URL}#unlock={pw}&t={ts}"

    print(f"\n{'=' * 60}")
    print(f"  Rsquare Studios — {link_type.title()} Link")
    print(f"{'=' * 60}")
    print(f"\n  {url}\n")
    print(f"  Expires: {expires.strftime('%b %d, %Y %I:%M %p')}")
    print(f"  (48 hours from now)\n")

    # Copy to clipboard on macOS
    try:
        import subprocess
        subprocess.run(["pbcopy"], input=url.encode(), check=True)
        print("  Copied to clipboard!\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
