#!/bin/bash
# UV Test Runner for Precinct App

set -e

echo "🧪 Running tests with UV..."

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

# Run tests with UV
echo "🔍 Running pytest with UV virtual environment..."
uv run pytest "$@"