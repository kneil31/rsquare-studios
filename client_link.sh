#!/bin/bash
# Generate a private client link for Rsquare Studios pricing
# Used by Apple Shortcut "Client Link" via Run Shell Script
# Outputs ONLY the shareable message (no decorations)

SECRET_FILE="$(dirname "$0")/.secret"

if [ ! -f "$SECRET_FILE" ]; then
  echo "Error: .secret not found"
  exit 1
fi

PW=$(python3 -c "import json; print(json.loads(open('$SECRET_FILE').read())['client'])")
TS=$(date +%s)
LINK="https://portfolio.rsquarestudios.com/?k=${PW}&t=${TS}&s=pricing"

cat <<EOF
Hey! Here's a private link to our portfolio and pricing 📷

${LINK}

This link is valid for 48 hours.
Let me know if you have any questions!
— Ram
EOF
