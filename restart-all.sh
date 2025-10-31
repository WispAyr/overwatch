#!/bin/bash

# Complete Overwatch Restart Script
# Kills all existing processes and relaunches everything

cd "$(dirname "$0")"

echo "🔄 Restarting Overwatch System..."
echo ""

# Kill existing processes
echo "🛑 Stopping existing processes..."
pkill -f "python.*backend/main.py" 2>/dev/null
pkill -f "python.*http.server.*7002" 2>/dev/null
pkill -f "vite.*workflow-builder" 2>/dev/null
pkill -f "mediamtx" 2>/dev/null
sleep 2
echo "✓ Processes stopped"
echo ""

# Free ports if still occupied
echo "🔓 Freeing ports..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:7001 | xargs kill -9 2>/dev/null  
lsof -ti:7002 | xargs kill -9 2>/dev/null
lsof -ti:7003 | xargs kill -9 2>/dev/null
lsof -ti:8554 | xargs kill -9 2>/dev/null
sleep 1
echo "✓ Ports freed"
echo ""

# Check venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: ./install.sh"
    exit 1
fi

# Create necessary directories
mkdir -p logs data/snapshots data/recordings models

echo "🚀 Starting services..."
echo ""

# Start Backend (port 8000)
echo "1️⃣  Starting Backend API (port 8000)..."
source venv/bin/activate
nohup python backend/main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
sleep 3

# Check backend started
if curl -s http://localhost:8000/api/system/status > /dev/null 2>&1; then
    echo "   ✓ Backend running on http://localhost:8000"
else
    echo "   ⚠️  Backend may still be starting..."
fi
echo ""

# Start Dashboard (port 7002) 
echo "2️⃣  Starting Dashboard (port 7002)..."
# Build CSS first
npm run build:css > /dev/null 2>&1
nohup python3 -m http.server 7002 --directory frontend > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "   PID: $DASHBOARD_PID"
sleep 2
echo "   ✓ Dashboard running on http://localhost:7002"
echo ""

# Start Workflow Builder (port 7003)
echo "3️⃣  Starting Workflow Builder (port 7003)..."
cd workflow-builder

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
fi

nohup npm run dev > ../logs/workflow-builder.log 2>&1 &
BUILDER_PID=$!
echo "   PID: $BUILDER_PID"
cd ..
sleep 3
echo "   ✓ Workflow Builder running on http://localhost:7003"
echo ""

echo "✅ All services started!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   🔧 Backend API:       http://localhost:8000"
echo "   📚 API Docs:          http://localhost:8000/docs"
echo "   🎛️  Dashboard:         http://localhost:7002"
echo "   🎨 Workflow Builder:  http://localhost:7003"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Process IDs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Backend:         $BACKEND_PID"
echo "   Dashboard:       $DASHBOARD_PID"
echo "   Workflow Builder: $BUILDER_PID"
echo ""
echo "To stop all services, run: ./stop-all.sh"
echo "To view logs: tail -f logs/*.log"
echo ""

