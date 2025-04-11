#!/bin/bash
# test-python-versions.sh - Test a workflow with Python 3.11 and 3.12

WORKFLOW_FILE=${1:-".github/workflows/ci.yml"}
EVENT_TYPE=${2:-"push"}
JOB_FILTER=${3:-""}
SKIP_DOCKER=${4:-false}

# Display header
echo "========================================"
echo "Testing workflow with Python 3.11 and 3.12"
echo "========================================"
echo "Workflow: $WORKFLOW_FILE"
echo "Event: $EVENT_TYPE"
if [ -n "$JOB_FILTER" ]; then
  echo "Job: $JOB_FILTER"
fi
if [ "$SKIP_DOCKER" = true ]; then
  echo "Mode: Direct (no Docker)"
else
  echo "Mode: Docker"
fi
echo "========================================"
echo ""

# Test with Python 3.11
echo "Testing with Python 3.11..."
echo "----------------------------------------"

if [ "$SKIP_DOCKER" = true ]; then
  .github/scripts/github-actions-test.sh --workflow "$WORKFLOW_FILE" --event "$EVENT_TYPE" --job "$JOB_FILTER" --python "3.11" --skip-docker
else
  .github/scripts/github-actions-test.sh --workflow "$WORKFLOW_FILE" --event "$EVENT_TYPE" --job "$JOB_FILTER" --python "3.11"
fi

PYTHON_311_EXIT=$?
echo "----------------------------------------"
echo ""

# Test with Python 3.12
echo "Testing with Python 3.12..."
echo "----------------------------------------"

if [ "$SKIP_DOCKER" = true ]; then
  .github/scripts/github-actions-test.sh --workflow "$WORKFLOW_FILE" --event "$EVENT_TYPE" --job "$JOB_FILTER" --python "3.12" --skip-docker
else
  .github/scripts/github-actions-test.sh --workflow "$WORKFLOW_FILE" --event "$EVENT_TYPE" --job "$JOB_FILTER" --python "3.12"
fi

PYTHON_312_EXIT=$?
echo "----------------------------------------"
echo ""

# Summary
echo "========================================"
echo "Test Summary"
echo "========================================"
if [ $PYTHON_311_EXIT -eq 0 ]; then
  echo "Python 3.11: ✅ PASSED"
else
  echo "Python 3.11: ❌ FAILED"
fi

if [ $PYTHON_312_EXIT -eq 0 ]; then
  echo "Python 3.12: ✅ PASSED"
else
  echo "Python 3.12: ❌ FAILED"
fi
echo "========================================"

# Return non-zero exit code if any test failed
if [ $PYTHON_311_EXIT -ne 0 ] || [ $PYTHON_312_EXIT -ne 0 ]; then
  exit 1
fi
