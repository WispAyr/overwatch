#!/bin/bash

# Start Overwatch Dashboard
# Builds CSS and serves frontend on port 7001

cd "$(dirname "$0")/.."

echo "Building Tailwind CSS..."
npm run build:css

echo "Starting dashboard on http://localhost:7002"
python3 -m http.server 7002 --directory frontend

