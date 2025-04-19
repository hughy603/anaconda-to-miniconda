#!/bin/bash
# Simple pre-push script that runs essential checks

echo "Running essential pre-push checks..."

# Check if pyright is available
if command -v pyright &> /dev/null; then
    echo "Running pyright type checking..."
    if ! pyright; then
        echo "ERROR: Pyright type checking failed. Fix the issues before pushing."
        exit 1
    fi
elif python -c "import pyright" &> /dev/null; then
    echo "Running pyright type checking..."
    if ! python -m pyright; then
        echo "ERROR: Pyright type checking failed. Fix the issues before pushing."
        exit 1
    fi
else
    echo "Pyright not found. Skipping type checking."
    echo "Consider installing pyright for better code quality: npm install -g pyright"
fi

echo "All essential checks passed. Proceeding with push."
exit 0
