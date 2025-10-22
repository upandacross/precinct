#!/bin/bash
# Stop Precinct App Script
# Kills any running Python processes for main.py or wsgi.py

set -e

echo "🛑 Stopping Precinct App processes..."

# Check for existing Python app processes
APP_PIDS=$(ps aux | grep -E '(python.*main\.py|python.*wsgi\.py)' | grep -v grep | awk '{print $2}' || true)

if [ ! -z "$APP_PIDS" ]; then
    echo "⚠️  Found existing Python app processes:"
    ps aux | grep -E '(python.*main\.py|python.*wsgi\.py)' | grep -v grep
    echo "🛑 Killing app processes: $APP_PIDS"
    echo $APP_PIDS | xargs kill -9 2>/dev/null || true
    sleep 2
else
    echo "✅ No Python app processes found"
fi

# Kill any processes on port 5000
PORT_PIDS=$(lsof -ti:5000 2>/dev/null || true)
if [ ! -z "$PORT_PIDS" ]; then
    echo "🛑 Killing processes on port 5000: $PORT_PIDS"
    echo $PORT_PIDS | xargs kill -9 2>/dev/null || true
    sleep 1
else
    echo "✅ No processes found on port 5000"
fi

# Final verification
REMAINING_APP=$(ps aux | grep -E '(python.*main\.py|python.*wsgi\.py)' | grep -v grep || true)
REMAINING_PORT=$(lsof -ti:5000 2>/dev/null || true)

if [ -z "$REMAINING_APP" ] && [ -z "$REMAINING_PORT" ]; then
    echo "✅ All app processes stopped successfully"
else
    echo "⚠️  Some processes may still be running:"
    [ ! -z "$REMAINING_APP" ] && echo "App processes:" && echo "$REMAINING_APP"
    [ ! -z "$REMAINING_PORT" ] && echo "Port 5000 processes:" && lsof -i:5000
fi