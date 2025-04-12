#!/bin/bash
# Script to run pre-commit on all files and fail if any checks fail

echo "Running pre-commit checks on all files before push..."
if ! pre-commit run --all-files; then
  echo "ERROR: Pre-commit checks failed. Fix the issues before pushing."
  echo "Run 'pre-commit run --all-files' to see and fix the issues."
  exit 1
fi

echo "All pre-commit checks passed. Proceeding with push."
exit 0