#!/bin/bash
# Setup script for Yeshua Architect Platform

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "⫰ Yeshua Architect Platform — Setup"

# Create venv
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[local]" 2>/dev/null || pip install -e .

# Create data directory
mkdir -p data/agents

# Initialize database
echo "Initializing database..."
python3 -c "import asyncio; from app.db import init_db; asyncio.run(init_db())"

# Download htmx if not present
if [ ! -f static/htmx.min.js ]; then
    echo "Downloading htmx..."
    curl -sL https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js -o static/htmx.min.js
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the platform:"
echo "  cd $DIR"
echo "  source .venv/bin/activate"
echo "  python -m app.main"
echo ""
echo "Then visit: http://localhost:8080"
