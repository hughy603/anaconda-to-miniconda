#!/bin/bash
# Simple pre-push script that runs essential checks

echo "Running essential pre-push checks..."

# Run type checking only (formatting happens at commit time)
echo "Running pyright type checking..."
if ! python -m pyright; then
  echo "ERROR: Pyright type checking failed. Fix the issues before pushing."
  exit 1
fi

echo "All essential checks passed. Proceeding with push."
exit 0
