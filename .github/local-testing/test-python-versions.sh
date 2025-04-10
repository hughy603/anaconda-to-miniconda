#!/bin/bash
# .github/local-testing/test-python-versions.sh

WORKFLOW_FILE=$1
EVENT_TYPE=${2:-push}

if [ -z "$WORKFLOW_FILE" ]; then
  echo "Usage: $0 <workflow-file> [event-type]"
  echo "Example: $0 .github/workflows/ci.yml pull_request"
  exit 1
fi

echo "Testing workflow with Python 3.11..."
.github/local-testing/test-workflow.sh "$WORKFLOW_FILE" "$EVENT_TYPE" "python-version=3.11"

echo ""
echo "Testing workflow with Python 3.12..."
.github/local-testing/test-workflow.sh "$WORKFLOW_FILE" "$EVENT_TYPE" "python-version=3.12"
