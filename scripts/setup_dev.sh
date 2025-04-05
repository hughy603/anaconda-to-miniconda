#!/bin/bash
set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

echo "Setting up development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Please install it with 'pipx install uv'"
    echo "See https://github.com/astral-sh/uv for more details"
    exit 1
fi

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "pre-commit is not installed. Installing with pipx..."
    pipx install pre-commit
fi

# Create requirements directory if it doesn't exist
mkdir -p requirements

# Generate requirements files
echo "Generating requirements files with uv..."
python scripts/update_deps.py

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv -p python3.11
fi

# Activate the virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    source .venv/Scripts/activate
fi

# Install dependencies
echo "Installing dependencies..."
uv pip install -e ".[dev,test]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install --install-hooks

echo "Development setup complete! ✅"
echo "To activate the virtual environment, run: source .venv/bin/activate (Linux/Mac) or .venv\\Scripts\\activate (Windows)"
