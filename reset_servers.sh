#!/bin/bash

# Fantasy Recaps Server Reset Script
# This script kills existing processes and restarts the development servers

echo "🔄 Fantasy Recaps - Server Reset Script"
echo "======================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    echo "🔪 Killing processes on port $port..."
    
    if check_port $port; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
        
        if check_port $port; then
            echo "⚠️  Warning: Port $port still has active processes"
            lsof -i:$port
        else
            echo "✅ Port $port cleared"
        fi
    else
        echo "✅ Port $port already free"
    fi
}

# Function to kill processes by name
kill_process_name() {
    local process_name=$1
    echo "🔪 Killing $process_name processes..."
    pkill -f "$process_name" 2>/dev/null || true
    sleep 1
}

echo ""
echo "🛑 Stopping existing servers..."

# Kill specific ports
kill_port 3000  # React frontend
kill_port 8000  # FastAPI backend
kill_port 3001  # Backup React port

# Kill specific process patterns
kill_process_name "react-scripts start"
kill_process_name "npm start"
kill_process_name "next-server"
kill_process_name "uvicorn"
kill_process_name "python3.*main:app"

echo ""
echo "🧹 Cleaning up..."
sleep 2

# Verify ports are clear
echo ""
echo "🔍 Checking port status..."
for port in 3000 8000 3001; do
    if check_port $port; then
        echo "❌ Port $port still occupied:"
        lsof -i:$port
    else
        echo "✅ Port $port is free"
    fi
done

echo ""
echo "🚀 Starting development servers..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Make sure you're in the project root directory."
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found."
    exit 1
fi

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found."
    exit 1
fi

# Start the servers using the npm script
echo "🎯 Starting both frontend and backend servers..."
echo ""
echo "Frontend will be available at: http://localhost:3000"
echo "Backend will be available at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Use npm run dev to start both servers
npm run dev
