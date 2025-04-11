#!/bin/bash
# A simplified script for testing GitHub Actions workflows locally

WORKFLOW_FILE=$1
EVENT_TYPE=${2:-push}
JOB_FILTER=$3
MATRIX_OVERRIDE=$4
ADDITIONAL_ARGS=${@:5}

# Validate inputs
if [ -z "$WORKFLOW_FILE" ]; then
  echo "Usage: $0 <workflow-file> [event-type] [job-filter] [matrix-override] [additional-args]"
  echo "Examples:"
  echo "  $0 .github/workflows/ci.yml"
  echo "  $0 .github/workflows/ci.yml pull_request"
  echo "  $0 .github/workflows/ci.yml test"
  echo "  $0 .github/workflows/ci.yml '' python-version=3.11"
  echo "  $0 .github/workflows/ci.yml push '' '' --verbose"
  exit 1
fi

# Create event file if it doesn't exist
mkdir -p .github/local-testing/events
if [ ! -f ".github/local-testing/events/$EVENT_TYPE.json" ]; then
  echo "Creating sample $EVENT_TYPE event..."
  echo '{
    "event_type": "'$EVENT_TYPE'"
  }' > .github/local-testing/events/$EVENT_TYPE.json
fi

# Build the command
CMD="act"

# Add workflow file
CMD="$CMD -W $WORKFLOW_FILE"

# Add event file
CMD="$CMD -e .github/local-testing/events/$EVENT_TYPE.json"

# Add job filter if provided
if [ -n "$JOB_FILTER" ]; then
  CMD="$CMD --job $JOB_FILTER"
fi

# Add matrix override if provided
if [ -n "$MATRIX_OVERRIDE" ]; then
  # Create a temporary JSON file for matrix inputs
  echo "Using matrix override: $MATRIX_OVERRIDE"

  # Parse matrix arguments
  IFS='=' read -r key value <<< "$MATRIX_OVERRIDE"

  echo "{
    \"$key\": \"$value\"
  }" > .github/local-testing/matrix-input.json

  CMD="$CMD --input-file .github/local-testing/matrix-input.json"
fi

# Add platform mappings
CMD="$CMD -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"
CMD="$CMD -P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04"
CMD="$CMD -P ubuntu-20.04=ghcr.io/catthehacker/ubuntu:act-20.04"
CMD="$CMD -P windows-latest=ghcr.io/catthehacker/ubuntu:act-latest"
CMD="$CMD -P macos-latest=ghcr.io/catthehacker/ubuntu:act-latest"

# Set environment variables for local testing
CMD="$CMD --env ACT_LOCAL_TESTING=true"
CMD="$CMD --env SKIP_DOCKER_BUILDS=true"
CMD="$CMD --env SKIP_LONG_RUNNING_TESTS=true"

# Add any additional arguments
if [ -n "$ADDITIONAL_ARGS" ]; then
  CMD="$CMD $ADDITIONAL_ARGS"
fi

# Run the command
echo "Running: $CMD"
eval $CMD
