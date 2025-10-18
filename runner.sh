#!/bin/bash

# Check for root (admin) privileges
if [ "$EUID" -ne 0 ]; then
  echo "Requesting administrative privileges..."
  sudo "$0" "$@"
  exit $?
fi

# Change to the script's directory
cd "$(dirname "$0")"

# Run the Python GUI in the background without terminal output
nohup python3 gui.py >/dev/null 2>&1 &

# Hide (exit the shell)
disown
exit 0
