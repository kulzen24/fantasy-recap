#!/bin/bash

# Fantasy Recaps - Frontend Only Script
# This script kills existing frontend processes and starts just the React development server

echo "🎯 Fantasy Recaps - Frontend Restart"
echo "===================================="

# Kill processes on port 3000 and 3001
echo "🔪 Killing existing frontend processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

echo "⏳ Waiting for processes to stop..."
sleep 3

# Check if ports are free
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null; then
    echo "⚠️  Warning: Port 3000 still occupied"
    lsof -i:3000
else
    echo "✅ Port 3000 is free"
fi

echo ""
echo "🚀 Starting React development server..."
echo "Frontend will be available at: http://localhost:3000"
echo ""

# Start just the frontend
npm run start:frontend
