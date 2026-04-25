#!/bin/bash
# Build/setup InsightBrowser Hosting
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

echo "=== InsightBrowser Hosting Setup ==="

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt -q

# Create directories
echo "Creating directories..."
mkdir -p data assets static

# Init database
echo "Initializing database..."
python3 -c "from models import init_db; init_db(); print('Database initialized')"

echo ""
echo "=== Setup Complete ==="
echo "Run: ./scripts/start.sh"
echo "Or: python3 main.py"
