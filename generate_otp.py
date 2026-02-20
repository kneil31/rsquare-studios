#!/usr/bin/env python3
"""
OTP Generator for Rsquare Studios Dashboard.

Generates a random client password, updates .secret, regenerates the dashboard,
pushes to GitHub Pages, and notifies via Slack.

Usage:
    python3 generate_otp.py              # Generate OTP + rebuild + push + Slack notify
    python3 generate_otp.py --no-push    # Generate + rebuild only (no git push, no Slack)
    python3 generate_otp.py --no-slack   # Generate + rebuild + push (no Slack)

The internal password (r2workflow) stays permanent.
Client OTP auto-expires when this script runs again (every 48h via LaunchAgent).
"""

import json
import os
import secrets
import string
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SECRET_FILE = SCRIPT_DIR / ".secret"
OTP_LOG_FILE = SCRIPT_DIR / ".otp_log.json"
GENERATE_SCRIPT = SCRIPT_DIR / "generate_dashboard.py"

# Slack config (reuse from Instagram AutoPoster)
SLACK_ENV = SCRIPT_DIR.parent / "Instagram_AutoPoster" / "scripts" / ".env"


def load_slack_creds():
    """Load Slack credentials from Instagram AutoPoster .env."""
    creds = {}
    if SLACK_ENV.exists():
        for line in SLACK_ENV.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                creds[key.strip()] = val.strip()
    return creds.get("SLACK_BOT_TOKEN"), creds.get("SLACK_CHANNEL_ID")


def generate_password(length=8):
    """Generate a readable random password (lowercase + digits, no ambiguous chars)."""
    # Exclude confusing chars: 0/O, 1/l/I
    chars = "abcdefghjkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(chars) for _ in range(length))


def update_secret(new_client_pw):
    """Update .secret file with new client password, keep internal password."""
    if SECRET_FILE.exists():
        data = json.loads(SECRET_FILE.read_text(encoding="utf-8"))
    else:
        print("ERROR: .secret file not found. Cannot update.")
        sys.exit(1)

    data["client"] = new_client_pw
    SECRET_FILE.write_text(json.dumps(data), encoding="utf-8")
    return data["internal"]


def log_otp(password):
    """Log OTP generation for tracking."""
    log = []
    if OTP_LOG_FILE.exists():
        try:
            log = json.loads(OTP_LOG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log = []

    log.append({
        "password": password,
        "generated": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(hours=48)).isoformat(),
    })

    # Keep last 20 entries only
    log = log[-20:]
    OTP_LOG_FILE.write_text(json.dumps(log, indent=2), encoding="utf-8")


def regenerate_dashboard():
    """Run generate_dashboard.py to rebuild index.html."""
    result = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT)],
        capture_output=True, text=True, cwd=str(SCRIPT_DIR)
    )
    if result.returncode != 0:
        print(f"ERROR: Dashboard generation failed:\n{result.stderr}")
        sys.exit(1)
    print("   Dashboard regenerated.")


def git_push():
    """Commit and push index.html to GitHub Pages."""
    subprocess.run(
        ["git", "add", "index.html"],
        cwd=str(SCRIPT_DIR), capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Rotate client OTP password"],
        cwd=str(SCRIPT_DIR), capture_output=True
    )
    result = subprocess.run(
        ["git", "push"],
        cwd=str(SCRIPT_DIR), capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"WARNING: git push failed:\n{result.stderr}")
        return False
    print("   Pushed to GitHub Pages.")
    return True


def notify_slack(password, expires):
    """Send OTP to Slack channel via HTTP API (no slack_sdk dependency)."""
    import urllib.request

    token, channel = load_slack_creds()
    if not token or not channel:
        print("   WARNING: Slack credentials not found, skipping notification.")
        return

    try:
        msg = (
            f"🔑 *New Dashboard OTP Generated*\n\n"
            f"Password: `{password}`\n"
            f"Expires: {expires}\n"
            f"Site: https://kneil31.github.io/rsquare-studios/\n\n"
            f"_Share this with the client for pricing access._"
        )
        payload = json.dumps({"channel": channel, "text": msg}).encode("utf-8")
        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode("utf-8"))
        if result.get("ok"):
            print("   Slack notification sent.")
        else:
            print(f"   WARNING: Slack API error: {result.get('error')}")
    except Exception as e:
        print(f"   WARNING: Slack notification failed: {e}")


def main():
    no_push = "--no-push" in sys.argv
    no_slack = "--no-slack" in sys.argv

    print("\n🔑 Generating new client OTP...")

    # Generate password
    password = generate_password()
    expires = (datetime.now() + timedelta(hours=48)).strftime("%b %d, %Y %I:%M %p")
    print(f"   Password: {password}")
    print(f"   Expires:  {expires}")

    # Update .secret
    update_secret(password)
    print("   .secret updated.")

    # Log it
    log_otp(password)

    # Regenerate
    regenerate_dashboard()

    # Push
    if not no_push:
        git_push()
    else:
        print("   Skipping git push (--no-push).")

    # Slack notify
    if not no_push and not no_slack:
        notify_slack(password, expires)
    else:
        print("   Skipping Slack notification.")

    print(f"\n✅ OTP ready! Share password '{password}' with client.\n")


if __name__ == "__main__":
    main()
