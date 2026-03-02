#!/usr/bin/env python3
"""
OTP Generator for Rsquare Studios Dashboard.

Generates a random client password, updates .secret, regenerates the dashboard,
pushes to GitHub Pages, and notifies via Slack.

Usage:
    python3 generate_otp.py              # Generate OTP + rebuild + push + Slack notify
    python3 generate_otp.py --no-push    # Generate + rebuild only (no git push, no Slack)
    python3 generate_otp.py --no-slack   # Generate + rebuild + push (no Slack)

The internal password (stored in .secret) stays permanent.
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
    # Sync to ~/.r2_secret for Apple Shortcut (SSH can't read Documents)
    home_secret = Path.home() / ".r2_secret"
    home_secret.write_text(json.dumps(data), encoding="utf-8")
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
        ["/opt/homebrew/bin/python3", str(GENERATE_SCRIPT)],
        capture_output=True, text=True, cwd=str(SCRIPT_DIR)
    )
    if result.returncode != 0:
        print(f"ERROR: Dashboard generation failed:\n{result.stderr}")
        return False
    print("   Dashboard regenerated.")
    return True


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


def notify_slack(password, expires, timestamp):
    """Send OTP to Slack channel via HTTP API (no slack_sdk dependency)."""
    import urllib.request

    token, channel = load_slack_creds()
    if not token or not channel:
        print("   WARNING: Slack credentials not found, skipping notification.")
        return

    unlock_url = f"https://portfolio.rsquarestudios.com/?k={password}&t={timestamp}&s=pricing"

    try:
        # Send client-ready message first (easy to copy-paste to WhatsApp)
        client_msg = (
            "Hey! Here's a private link to our portfolio and pricing 📷\n\n"
            f"{unlock_url}\n\n"
            "Let me know if you have any questions!\n"
            "— Ram"
        )
        payload_pw = json.dumps({
            "channel": channel,
            "text": client_msg,
        }).encode("utf-8")
        req_pw = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=payload_pw,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        urllib.request.urlopen(req_pw, timeout=10)

        # Then send internal context message
        msg = f"🔑 OTP generated — expires {expires}\n🔗 {unlock_url}"
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

    # Generate password + timestamp
    password = generate_password()
    timestamp = int(datetime.now().timestamp())
    expires = (datetime.now() + timedelta(hours=48)).strftime("%b %d, %Y %I:%M %p")
    unlock_url = f"https://portfolio.rsquarestudios.com/?k={password}&t={timestamp}&s=pricing"
    print(f"   Password: {password}")
    print(f"   Link:     {unlock_url}")
    print(f"   Expires:  {expires}")

    # Save old password for rollback
    old_secret = SECRET_FILE.read_text(encoding="utf-8")

    # Update .secret FIRST (dashboard reads it during generation)
    update_secret(password)
    print("   .secret updated.")

    # Regenerate — if this fails, rollback .secret
    if not regenerate_dashboard():
        print("   ROLLING BACK .secret to previous password...")
        SECRET_FILE.write_text(old_secret, encoding="utf-8")
        home_secret = Path.home() / ".r2_secret"
        home_secret.write_text(old_secret, encoding="utf-8")
        print("   Rollback complete. Dashboard unchanged.")
        sys.exit(1)

    # Log it (only after successful rebuild)
    log_otp(password)

    # Push
    pushed = True
    if not no_push:
        pushed = git_push()
        if not pushed:
            print("   WARNING: Push failed — dashboard rebuilt locally but not deployed.")
    else:
        print("   Skipping git push (--no-push).")

    # Slack notify (only if push succeeded)
    if not no_push and not no_slack and pushed:
        notify_slack(password, expires, timestamp)
    elif not pushed:
        print("   Skipping Slack notification (push failed).")
    else:
        print("   Skipping Slack notification.")

    print(f"\n✅ OTP ready! Link copied to Slack — just forward to client.\n")


if __name__ == "__main__":
    main()
