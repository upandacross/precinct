#!/bin/bash
# UV Development Setup for Precinct App
# Adds development dependencies and tools

set -e

echo "🛠️ Setting up development environment with UV..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Please run ./setup-uv.sh first"
    exit 1
fi

# Ensure we have the latest uv
echo "📦 Updating UV to latest version..."
uv self update

# Add development dependencies if they don't exist
echo "🔧 Adding development dependencies..."
uv add --group dev pytest-flask
uv add --group dev dash plotly pandas  # For analytics

# Add pre-commit tools
echo "🎯 Adding code quality tools..."
uv add --group dev pre-commit

# Install pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
uv run pre-commit install 2>/dev/null || echo "Pre-commit hooks setup failed - continuing..."

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Available commands:"
echo "   ./run-app.sh         - Start the Flask app"
echo "   ./run-tests.sh       - Run all tests"
echo "   uv run python <file> - Run any Python script"
echo "   uv add <package>     - Add new dependencies"
echo "   uv remove <package>  - Remove dependencies"
echo "   uv sync              - Sync dependencies"
echo ""
echo "🔧 Development tools:"
echo "   uv run black .       - Format code"
echo "   uv run isort .       - Sort imports"
echo "   uv run flake8 .      - Lint code"
echo "   uv run mypy .        - Type checking"