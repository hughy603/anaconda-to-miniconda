#!/bin/bash
# Script to test a workflow with different Python versions

WORKFLOW_FILE=$1
EVENT_TYPE=${2:-push}
JOB_FILTER=$3
ADDITIONAL_ARGS=${@:4}

if [ -z "$WORKFLOW_FILE" ]; then
  echo "Usage: $0 <workflow-file> [event-type] [job-filter] [additional-args]"
  echo "Examples:"
  echo "  $0 .github/workflows/ci.yml"
  echo "  $0 .github/workflows/ci.yml pull_request"
  echo "  $0 .github/workflows/ci.yml test"
  echo "  $0 .github/workflows/ci.yml push test --verbose"
  exit 1
fi

echo "Testing workflow with Python 3.11..."
.github/local-testing/local-test.sh "$WORKFLOW_FILE" "$EVENT_TYPE" "$JOB_FILTER" "python-version=3.11" $ADDITIONAL_ARGS

echo ""
echo "Testing workflow with Python 3.12..."
.github/local-testing/local-test.sh "$WORKFLOW_FILE" "$EVENT_TYPE" "$JOB_FILTER" "python-version=3.12" $ADDITIONAL_ARGS
