#!/bin/bash
# File: .vscode/scripts/validate-workflows.sh

# Get the file path from the first argument
FILE_PATH="$1"

# Only run on workflow files
if [[ "$FILE_PATH" == .github/workflows/* ]] || [[ "$FILE_PATH" == .github/actions/*/action.yml ]]; then
  # Run pre-commit on the specific file
  pre-commit run actionlint --files "$FILE_PATH"
else
  echo "Not a GitHub Actions workflow file, skipping validation."
  exit 0
fi
