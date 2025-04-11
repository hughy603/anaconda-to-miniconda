#!/bin/bash
# validate-workflow.sh - Validate GitHub Actions workflow files

WORKFLOW_FILE=${1:-".github/workflows/ci.yml"}

if [ ! -f "$WORKFLOW_FILE" ]; then
  echo "Error: Workflow file not found: $WORKFLOW_FILE"
  echo "Usage: $0 [workflow-file]"
  exit 1
fi

echo "Validating workflow: $WORKFLOW_FILE"

# Check if actionlint is installed
if command -v actionlint &> /dev/null; then
  echo "Running actionlint..."
  actionlint "$WORKFLOW_FILE"
  ACTIONLINT_EXIT=$?
  if [ $ACTIONLINT_EXIT -ne 0 ]; then
    echo "actionlint found issues in the workflow file."
  fi
else
  echo "Warning: actionlint not found. Install with: 'go install github.com/rhysd/actionlint/cmd/actionlint@latest'"
  echo "Continuing with basic checks..."
fi

echo "Running custom checks..."

# Check for Python version matrix
if grep -q "matrix:" "$WORKFLOW_FILE"; then
  echo "Matrix strategy found"

  if grep -q "python-version:" "$WORKFLOW_FILE"; then
    echo "Python versions specified in matrix"

    # Check if Python 3.11 and 3.12 are included
    if ! grep -q "3.11" "$WORKFLOW_FILE"; then
      echo "WARNING: Matrix should include Python 3.11"
    fi

    if ! grep -q "3.12" "$WORKFLOW_FILE"; then
      echo "WARNING: Matrix should include Python 3.12"
    fi
  else
    echo "WARNING: Matrix strategy found but no Python versions specified"
  fi
else
  echo "WARNING: No matrix strategy found in workflow"
fi

# Check for conditional execution for local testing
if ! grep -q "ACT_LOCAL_TESTING" "$WORKFLOW_FILE"; then
  echo "WARNING: Workflow does not have conditional execution for local testing"
  echo "Consider adding: if: \${{ env.ACT_LOCAL_TESTING != 'true' }} for steps that shouldn't run locally"
fi

# Check for deprecated actions
if grep -q "uses: actions/[^@]*@master" "$WORKFLOW_FILE"; then
  echo "ERROR: Uses actions with @master tag instead of version tag"
  echo "Replace @master with specific version tags like @v4"
fi

# Check for hardcoded Python versions
if grep -q "python-version: \"3\.[0-9][0-9]*\"" "$WORKFLOW_FILE" || grep -q "python-version: '3\.[0-9][0-9]*'" "$WORKFLOW_FILE"; then
  echo "WARNING: Hardcoded Python version found. Consider using matrix or environment variables."
fi

# Check for proper environment variable usage
if ! grep -q "env:" "$WORKFLOW_FILE"; then
  echo "TIP: Consider using environment variables for common values"
fi

# Check for proper cache usage
if grep -q "actions/cache" "$WORKFLOW_FILE" && ! grep -q "actions/cache@v4" "$WORKFLOW_FILE"; then
  echo "WARNING: Using outdated version of actions/cache. Consider upgrading to v4."
fi

echo "Validation complete"

# Return non-zero exit code if actionlint failed
if [ -n "$ACTIONLINT_EXIT" ] && [ $ACTIONLINT_EXIT -ne 0 ]; then
  exit $ACTIONLINT_EXIT
fi
