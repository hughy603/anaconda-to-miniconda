#!/bin/bash
# Script to update the CI workflow file with conditional execution for local testing

CI_WORKFLOW=".github/workflows/ci.yml"

# Check if the workflow file exists
if [ ! -f "$CI_WORKFLOW" ]; then
  echo "Error: CI workflow file not found: $CI_WORKFLOW"
  exit 1
fi

# Create a backup of the original file
cp "$CI_WORKFLOW" "$CI_WORKFLOW.bak"
echo "Created backup: $CI_WORKFLOW.bak"

# Add ACT_LOCAL_TESTING environment variable if it doesn't exist
if ! grep -q "ACT_LOCAL_TESTING" "$CI_WORKFLOW"; then
  echo "Adding ACT_LOCAL_TESTING environment variable..."
  # Find the env section and add the variable
  sed -i '/^env:/a\  ACT_LOCAL_TESTING: ${{ vars.ACT_LOCAL_TESTING || '\''false'\'' }}' "$CI_WORKFLOW"
fi

# Update matrix configuration for conditional execution
echo "Updating matrix configuration for conditional execution..."
# Find the matrix section and update it
sed -i 's/python-version: \[\("3.11", "3.12"\)\]/python-version: ${{ env.ACT_LOCAL_TESTING == '\''true'\'' \&\& fromJSON('\''["3.11"]'\'') || fromJSON('\''["3.11", "3.12"]'\'') }}/g' "$CI_WORKFLOW"
sed -i 's/os: \[\("ubuntu-latest", "windows-latest", "macos-latest"\)\]/os: ${{ env.ACT_LOCAL_TESTING == '\''true'\'' \&\& fromJSON('\''["ubuntu-latest"]'\'') || fromJSON('\''["ubuntu-latest", "windows-latest", "macos-latest"]'\'') }}/g' "$CI_WORKFLOW"

# Add conditional execution for steps that shouldn't run locally
echo "Adding conditional execution for steps that shouldn't run locally..."

# Find the Upload coverage to Codecov step and add conditional
sed -i '/Upload coverage to Codecov/,/codecov-action/{s/if: matrix.os == '\''ubuntu-latest'\''/if: matrix.os == '\''ubuntu-latest'\'' \&\& env.ACT_LOCAL_TESTING != '\''true'\''/}' "$CI_WORKFLOW"

# Find the Run security checks step and add conditional
sed -i '/Run security checks/,/security/{s/if: matrix.os == '\''ubuntu-latest'\'' \&\& matrix.python-version == '\''3.11'\''/if: matrix.os == '\''ubuntu-latest'\'' \&\& matrix.python-version == '\''3.11'\'' \&\& env.ACT_LOCAL_TESTING != '\''true'\''/}' "$CI_WORKFLOW"

echo "CI workflow file updated successfully!"
echo "You can now test it with: .github/scripts/test-github-actions.sh"
