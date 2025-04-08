#!/bin/sh
set -e

echo "Starting hot-potato service..."

# Optional: Add commands for pre-startup tasks here, e.g.:
# python database.py --backup

# Start the main application.
exec PYTHONPATH=. python ./src/main.py
