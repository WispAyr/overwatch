#!/bin/bash
set -e

echo "🚀 Overwatch Installation Script"
echo "================================"
echo ""

cd "$(dirname "$0")"

# Check Python
echo "1️⃣  Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10 or later."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "   ✅ Found $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "2️⃣  Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Created venv"
else
    echo "   ✅ venv already exists"
fi
echo ""

# Activate and install dependencies
echo "3️⃣  Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "   ✅ Python packages installed"
echo ""

# Install Node dependencies
echo "4️⃣  Installing Node.js dependencies..."
if ! command -v npm &> /dev/null; then
    echo "   ⚠️  npm not found - skipping frontend build"
    echo "   You can install Node.js from: https://nodejs.org/"
else
    npm install
    echo "   ✅ Node packages installed"
fi
echo ""

# Build frontend
echo "5️⃣  Building frontend CSS..."
if command -v npm &> /dev/null; then
    npm run build:css
    echo "   ✅ CSS built"
else
    echo "   ⚠️  Skipped (npm not available)"
fi
echo ""

# Create directories
echo "6️⃣  Creating data directories..."
mkdir -p logs data/snapshots data/recordings models config
echo "   ✅ Directories created"
echo ""

# Download model
echo "7️⃣  Downloading YOLOv8n model (this may take a minute)..."
if [ ! -f "models/yolov8n.pt" ]; then
    python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 2>/dev/null || true
    if [ -f "yolov8n.pt" ]; then
        mv yolov8n.pt models/
    fi
    echo "   ✅ Model ready"
else
    echo "   ✅ Model already exists"
fi
echo ""

echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Start backend:  source venv/bin/activate && python backend/main.py"
echo "2. Start frontend: ./scripts/start_dashboard.sh"
echo "3. Open browser:   http://localhost:7002"
echo ""

