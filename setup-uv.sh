#!/bin/bash
# UV Environment Setup Script for Precinct App
# Makes uv the constant virtual environment management tool

set -e  # Exit on any error

echo "🔧 Setting up UV virtual environment for Precinct App..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✅ UV installed successfully"
fi

# Display UV version
echo "📦 UV Version: $(uv --version)"

# Create/sync virtual environment with uv
echo "🌟 Creating UV virtual environment..."
uv venv --python 3.11

# Activate the virtual environment
source .venv/bin/activate

# Sync dependencies with uv (this reads pyproject.toml)
echo "📥 Installing dependencies with UV..."
uv sync

# Install development dependencies
echo "📥 Installing development dependencies..."
uv sync --group dev

echo "✅ UV virtual environment setup complete!"
echo ""
echo "🎯 To activate the environment manually:"
echo "   source .venv/bin/activate"
echo ""
echo "🚀 To run the app:"
echo "   uv run python main.py"
echo ""
echo "🧪 To run tests:"
echo "   uv run pytest"
echo ""
echo "📦 To add new dependencies:"
echo "   uv add package-name"
echo ""
echo "🔧 To remove dependencies:"
echo "   uv remove package-name"