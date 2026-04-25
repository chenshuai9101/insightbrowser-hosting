#!/bin/bash
# Start InsightBrowser Hosting
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"
echo "Starting InsightBrowser Hosting on port 7001..."
python3 main.py
