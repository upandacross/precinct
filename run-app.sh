#!/bin/bash
# UV Run Script for Precinct App
# Ensures the app always runs with UV virtual environment

set -e

echo "🚀 Starting Precinct App with UV..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Please run ./setup-uv.sh first"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Running setup..."
    ./setup-uv.sh
fi

# Check for existing Python app processes
echo "🔍 Checking for existing Python app processes..."
APP_PIDS=$(ps aux | grep -E '(python.*main\.py|python.*wsgi\.py)' | grep -v grep | awk '{print $2}' || true)

if [ ! -z "$APP_PIDS" ]; then
    echo "⚠️  Found existing Python app processes:"
    ps aux | grep -E '(python.*main\.py|python.*wsgi\.py)' | grep -v grep
    echo "🛑 Killing existing app processes: $APP_PIDS"
    echo $APP_PIDS | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Kill any remaining processes on port 5000
echo "🔍 Checking for remaining processes on port 5000..."
PORT_PIDS=$(lsof -ti:5000 2>/dev/null || true)
if [ ! -z "$PORT_PIDS" ]; then
    echo "🛑 Killing processes on port 5000: $PORT_PIDS"
    echo $PORT_PIDS | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Verify port is clear
if lsof -ti:5000 >/dev/null 2>&1; then
    echo "❌ Port 5000 is still occupied. Please check manually:"
    lsof -i:5000
    exit 1
fi

# Run the Flask app with UV
echo "🌟 Starting Flask app with UV virtual environment..."
uv run python main.py &
APP_PID=$!

# Give the app a moment to start up
echo "⏳ Waiting for app to initialize..."
sleep 3

# Check if the app is running
if kill -0 $APP_PID 2>/dev/null; then
    echo "✅ App started successfully! (PID: $APP_PID)"
    echo "🌐 Access the app at: http://localhost:5000"
    echo "📱 Or on your network at: http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "💡 Press Ctrl+C to stop the app"
    
    # Wait for the background process
    wait $APP_PID
else
    echo "❌ App failed to start"
    exit 1
fi