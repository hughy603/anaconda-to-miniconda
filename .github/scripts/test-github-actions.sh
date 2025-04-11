#!/bin/bash
# Simplified script for testing GitHub Actions workflows with Python 3.11 and 3.12
# This script combines the functionality of multiple scripts into one

# Default values
WORKFLOW_FILE=".github/workflows/ci.yml"
EVENT_TYPE="push"
JOB_FILTER=""
PYTHON_VERSION=""
SKIP_DOCKER=false
TEST_BOTH_VERSIONS=false

# Display help
function show_help {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --workflow, -w FILE    Workflow file to test (default: .github/workflows/ci.yml)"
  echo "  --event, -e TYPE       Event type (default: push)"
  echo "  --job, -j NAME         Job to run (default: all jobs)"
  echo "  --python, -p VERSION   Python version to test (default: use matrix)"
  echo "  --both-versions, -b    Test with both Python 3.11 and 3.12"
  echo "  --skip-docker, -s      Skip Docker and run tests directly with local Python"
  echo "  --validate, -v         Validate workflow file only"
  echo "  --help, -h             Show this help message"
  exit 0
}

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
    --both-versions|-b)
      TEST_BOTH_VERSIONS=true
      shift
      ;;
    --skip-docker|-s)
      SKIP_DOCKER=true
      shift
      ;;
    --validate|-v)
      VALIDATE_ONLY=true
      shift
      ;;
    --help|-h)
      show_help
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      ;;
  esac
done

# Validate workflow file
function validate_workflow {
  echo "Validating workflow: $WORKFLOW_FILE"

  # Check if actionlint is installed
  if command -v actionlint &> /dev/null; then
    echo "Running actionlint..."
    actionlint "$WORKFLOW_FILE"
    ACTIONLINT_EXIT=$?
    if [ $ACTIONLINT_EXIT -ne 0 ]; then
      echo "actionlint found issues in the workflow file."
      return $ACTIONLINT_EXIT
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
    return 1
  fi

  echo "Validation complete"
  return 0
}

# If validate only, run validation and exit
if [ "$VALIDATE_ONLY" = true ]; then
  validate_workflow
  exit $?
fi

# Create event file if it doesn't exist
mkdir -p .github/local-testing/events
if [ ! -f ".github/local-testing/events/$EVENT_TYPE.json" ]; then
  echo "Creating sample $EVENT_TYPE event..."
  echo '{
    "event_type": "'$EVENT_TYPE'"
  }' > .github/local-testing/events/$EVENT_TYPE.json
fi

# Function to run tests with a specific Python version
function run_tests_with_python {
  local python_version=$1
  echo "Testing with Python $python_version..."
  echo "----------------------------------------"

  if [ "$SKIP_DOCKER" = true ]; then
    echo "Running tests directly with Python $python_version..."

    # Check if the Python version is available
    if ! command -v python$python_version &> /dev/null; then
      echo "Python $python_version not found. Please install it or use Docker."
      return 1
    fi

    # Extract test commands from workflow
    TEST_COMMAND=$(grep -A 5 "Run tests" "$WORKFLOW_FILE" | grep -oP 'run: \K.*' | head -1)

    # Use hatch or poetry based on what's available
    if command -v hatch &> /dev/null; then
      echo "Using hatch to run tests..."
      hatch env create python$python_version
      hatch run test
    elif command -v poetry &> /dev/null; then
      echo "Using poetry to run tests..."
      poetry env use $python_version
      poetry install
      poetry run pytest
    else
      echo "Neither hatch nor poetry found. Using system Python..."
      python$python_version -m pytest
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

    # Add matrix override for Python version
    echo "Using Python version: $python_version"
    echo "{
      \"python-version\": \"$python_version\"
    }" > .github/local-testing/matrix-input.json

    CMD="$CMD --input-file .github/local-testing/matrix-input.json"

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

  return $?
}

# Validate the workflow file first
validate_workflow
if [ $? -ne 0 ]; then
  echo "Workflow validation failed. Fix the issues before testing."
  exit 1
fi

# Test with both Python versions if requested
if [ "$TEST_BOTH_VERSIONS" = true ]; then
  echo "========================================"
  echo "Testing workflow with Python 3.11 and 3.12"
  echo "========================================"

  # Test with Python 3.11
  run_tests_with_python "3.11"
  PYTHON_311_EXIT=$?

  # Test with Python 3.12
  run_tests_with_python "3.12"
  PYTHON_312_EXIT=$?

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

  exit 0
fi

# Test with specific Python version if provided
if [ -n "$PYTHON_VERSION" ]; then
  run_tests_with_python "$PYTHON_VERSION"
  exit $?
fi

# If no Python version specified, run with default settings
if [ "$SKIP_DOCKER" = true ]; then
  echo "Running tests with default Python version..."

  # Use hatch or poetry based on what's available
  if command -v hatch &> /dev/null; then
    echo "Using hatch to run tests..."
    hatch run test
  elif command -v poetry &> /dev/null; then
    echo "Using poetry to run tests..."
    poetry install
    poetry run pytest
  else
    echo "Neither hatch nor poetry found. Using system Python..."
    python -m pytest
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
