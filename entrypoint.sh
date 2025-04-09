#!/bin/sh
set -e

echo "Starting hot-potato service..."

# Optional: Add commands for pre-startup tasks here, e.g.:
# python database.py --backup

# Define PYTHONPATH e executa o app
export PYTHONPATH=.
exec python src/main.py
