#!/bin/bash
# .github/local-testing/test-workflow.sh

WORKFLOW_FILE=$1
EVENT_TYPE=${2:-push}
MATRIX_OVERRIDE=$3

if [ -z "$WORKFLOW_FILE" ]; then
  echo "Usage: $0 <workflow-file> [event-type] [matrix-override]"
  echo "Examples:"
  echo "  $0 .github/workflows/ci.yml"
  echo "  $0 .github/workflows/ci.yml pull_request"
  echo "  $0 .github/workflows/ci.yml push python-version=3.11"
  exit 1
fi

# Create events directory if it doesn't exist
mkdir -p .github/local-testing/events

# Create a simple event file if it doesn't exist
if [ ! -f ".github/local-testing/events/$EVENT_TYPE.json" ]; then
  echo "Creating sample $EVENT_TYPE event..."
  echo '{
    "event_type": "'$EVENT_TYPE'"
  }' > .github/local-testing/events/$EVENT_TYPE.json
fi

# Handle matrix override
if [ -n "$MATRIX_OVERRIDE" ]; then
  echo "Using matrix override: $MATRIX_OVERRIDE"

  # Create a temporary JSON file for matrix inputs
  echo "{" > .github/local-testing/matrix-input.json

  # Parse matrix arguments
  IFS='=' read -r key value <<< "$MATRIX_OVERRIDE"
  echo "  \"$key\": \"$value\"" >> .github/local-testing/matrix-input.json

  # Close the JSON
  echo "}" >> .github/local-testing/matrix-input.json

  # Run with matrix override
  echo "Testing workflow: $WORKFLOW_FILE with event: $EVENT_TYPE and matrix: $MATRIX_OVERRIDE"
  act -W "$WORKFLOW_FILE" -e .github/local-testing/events/$EVENT_TYPE.json --input-file .github/local-testing/matrix-input.json
else
  # Run without matrix override
  echo "Testing workflow: $WORKFLOW_FILE with event: $EVENT_TYPE"
  act -W "$WORKFLOW_FILE" -e .github/local-testing/events/$EVENT_TYPE.json
fi

