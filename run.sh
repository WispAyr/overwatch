#!/bin/bash

# Simple script to run Overwatch backend

cd "$(dirname "$0")"

echo "🎯 Starting Overwatch Backend..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: ./install.sh"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if required packages are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo "Please run: ./install.sh"
    exit 1
fi

# Create necessary directories
mkdir -p logs data/snapshots data/recordings models

# Run Overwatch
echo "Starting Overwatch..."
echo "API: http://localhost:8000"
echo "Dashboard: http://localhost:7002"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python backend/main.py

