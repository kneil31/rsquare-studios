#!/bin/bash
# Editor reminder summary — for iPhone Shortcut SSH
# Usage: ./editor_reminder.sh [--editor NAME] [--feedback]
# Output: WhatsApp-ready message to stdout

cd "$(dirname "$0")"
/opt/homebrew/bin/python3 editor_reminder_summary.py "$@"
