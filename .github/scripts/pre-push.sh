#!/bin/bash
# Simple pre-push script that runs essential checks

echo "Running essential pre-push checks..."

# Run ruff linting and formatting
echo "Running ruff linting and formatting..."
if ! ruff check --fix .; then
  echo "ERROR: Ruff linting failed. Fix the issues before pushing."
  exit 1
fi

if ! ruff format .; then
  echo "ERROR: Ruff formatting failed. Fix the issues before pushing."
  exit 1
fi

# Run pyright type checking
echo "Running pyright type checking..."
if ! pyright; then
  echo "ERROR: Pyright type checking failed. Fix the issues before pushing."
  exit 1
fi

echo "All essential checks passed. Proceeding with push."
exit 0