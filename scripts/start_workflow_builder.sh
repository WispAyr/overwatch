#!/bin/bash

# Start Overwatch Workflow Builder

cd "$(dirname "$0")/../workflow-builder"

echo "🎨 Starting Overwatch Workflow Builder..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

echo "Starting development server on http://localhost:7003"
echo "Press Ctrl+C to stop"
echo ""

npm run dev


