#!/bin/bash

# Stop all Overwatch services

cd "$(dirname "$0")"

echo "🛑 Stopping Overwatch services..."
echo ""

# Kill processes by name
echo "Stopping Backend..."
pkill -f "python.*backend/main.py"

echo "Stopping Dashboard..."
pkill -f "python.*http.server.*7002"

echo "Stopping Workflow Builder..."
pkill -f "vite.*workflow-builder"

echo "Stopping MediaMTX..."
pkill -f "mediamtx"

sleep 2

# Force kill ports if still occupied
echo ""
echo "Freeing ports..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:7001 | xargs kill -9 2>/dev/null
lsof -ti:7002 | xargs kill -9 2>/dev/null
lsof -ti:7003 | xargs kill -9 2>/dev/null
lsof -ti:8554 | xargs kill -9 2>/dev/null

echo ""
echo "✅ All services stopped"

