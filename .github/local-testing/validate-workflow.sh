#!/bin/bash
# Script to validate GitHub Actions workflow files

WORKFLOW_FILE=$1

if [ -z "$WORKFLOW_FILE" ]; then
  echo "Usage: $0 <workflow-file>"
  echo "Example: $0 .github/workflows/ci.yml"
  exit 1
fi

# Check if the workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
  echo "Error: Workflow file not found: $WORKFLOW_FILE"
  exit 1
fi

# Check if actionlint is installed
if ! command -v actionlint &> /dev/null; then
  echo "Warning: actionlint is not installed. Installing..."

  # Try to install actionlint
  if command -v curl &> /dev/null; then
    bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)
    echo "actionlint installed successfully."
  else
    echo "Error: curl is not installed. Please install actionlint manually:"
    echo "https://github.com/rhysd/actionlint#installation"
    exit 1
  fi
fi

# Run actionlint
echo "Validating workflow: $WORKFLOW_FILE"
actionlint "$WORKFLOW_FILE"
ACTIONLINT_EXIT_CODE=$?

# Additional custom checks
echo "Running custom checks..."

# Check for common issues
if grep -q "uses: actions/checkout@master" "$WORKFLOW_FILE"; then
  echo "ERROR: Uses actions/checkout@master instead of a version tag"
  exit 1
fi

if grep -q "uses: actions/setup-python@master" "$WORKFLOW_FILE"; then
  echo "ERROR: Uses actions/setup-python@master instead of a version tag"
  exit 1
fi

# Check for matrix strategy
if grep -q "matrix:" "$WORKFLOW_FILE"; then
  echo "Matrix strategy found"

  # Check if Python versions are specified
  if grep -q "python-version:" "$WORKFLOW_FILE"; then
    echo "Python versions specified in matrix"

    # Check if Python 3.11 and 3.12 are included
    if ! grep -q "3.11" "$WORKFLOW_FILE" || ! grep -q "3.12" "$WORKFLOW_FILE"; then
      echo "WARNING: Matrix should include Python 3.11 and 3.12"
    fi
  fi
fi

# Check for environment variables for local testing
if ! grep -q "ACT_LOCAL_TESTING" "$WORKFLOW_FILE"; then
  echo "WARNING: Workflow does not contain conditionals for local testing (ACT_LOCAL_TESTING)"
  echo "Consider adding conditionals to make the workflow compatible with local testing:"
  echo "Example:"
  echo "  if: \${{ env.ACT_LOCAL_TESTING != 'true' }}"
  echo "  or"
  echo "  if [[ \"\${{ env.ACT_LOCAL_TESTING }}\" == \"true\" ]]; then"
  echo "    # Simplified version for local testing"
  echo "  else"
  echo "    # Full version for GitHub"
  echo "  fi"
fi

# Check for hardcoded secrets
if grep -q "GITHUB_TOKEN:" "$WORKFLOW_FILE"; then
  echo "WARNING: Workflow contains hardcoded GITHUB_TOKEN reference"
  echo "Consider using \${{ secrets.GITHUB_TOKEN }} instead"
fi

# Final status
if [ $ACTIONLINT_EXIT_CODE -eq 0 ]; then
  echo "Validation complete. No actionlint errors found."
else
  echo "Validation complete. actionlint found errors."
  exit $ACTIONLINT_EXIT_CODE
fi
