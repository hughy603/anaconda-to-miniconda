#!/bin/bash
# github-actions-test.sh - A simplified script for testing GitHub Actions

# Default values
WORKFLOW_FILE=".github/workflows/ci.yml"
EVENT_TYPE="push"
JOB_FILTER=""
PYTHON_VERSION=""
SKIP_DOCKER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --workflow|-w)
      WORKFLOW_FILE="$2"
      shift 2
      ;;
    --event|-e)
      EVENT_TYPE="$2"
      shift 2
      ;;
    --job|-j)
      JOB_FILTER="$2"
      shift 2
      ;;
    --python|-p)
      PYTHON_VERSION="$2"
      shift 2
      ;;
    --skip-docker|-s)
      SKIP_DOCKER=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --workflow, -w FILE    Workflow file to test (default: .github/workflows/ci.yml)"
      echo "  --event, -e TYPE       Event type (default: push)"
      echo "  --job, -j NAME         Job to run (default: all jobs)"
      echo "  --python, -p VERSION   Python version to test (default: use matrix)"
      echo "  --skip-docker, -s      Skip Docker and run tests directly with local Python"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create event file if it doesn't exist
mkdir -p .github/local-testing/events
if [ ! -f ".github/local-testing/events/$EVENT_TYPE.json" ]; then
  echo "Creating sample $EVENT_TYPE event..."
  echo '{
    "event_type": "'$EVENT_TYPE'"
  }' > .github/local-testing/events/$EVENT_TYPE.json
fi

if [ "$SKIP_DOCKER" = true ]; then
  echo "Running tests directly with local Python..."

  # Extract test commands from workflow
  TEST_COMMAND=$(grep -A 5 "Run tests" "$WORKFLOW_FILE" | grep -oP 'run: \K.*' | head -1)

  if [ -n "$PYTHON_VERSION" ]; then
    echo "Testing with Python $PYTHON_VERSION..."
    # Use poetry to run tests with specific Python version
    poetry env use $PYTHON_VERSION
    poetry install
    poetry run $TEST_COMMAND
  else
    echo "Testing with default Python version..."
    poetry install
    poetry run $TEST_COMMAND
  fi
else
  # Build the act command
  CMD="act"

  # Add workflow file
  CMD="$CMD -W $WORKFLOW_FILE"

  # Add event file
  CMD="$CMD -e .github/local-testing/events/$EVENT_TYPE.json"

  # Add job filter if provided
  if [ -n "$JOB_FILTER" ]; then
    CMD="$CMD --job $JOB_FILTER"
  fi

  # Add matrix override if Python version is provided
  if [ -n "$PYTHON_VERSION" ]; then
    echo "Using Python version: $PYTHON_VERSION"
    echo "{
      \"python-version\": \"$PYTHON_VERSION\"
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

  # Run the command
  echo "Running: $CMD"
  eval $CMD
fi
