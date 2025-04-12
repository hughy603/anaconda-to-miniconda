#!/bin/bash
# Simple script for running GitHub Actions workflows locally using act
# This follows industry standard practices for local GitHub Actions testing

# Display help information
function show_help {
  echo "GitHub Actions Local Testing"
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -w, --workflow FILE     Workflow file to run (required)"
  echo "  -e, --event TYPE        Event type to trigger (default: push)"
  echo "  -j, --job JOB           Run specific job"
  echo "  -p, --platform PLATFORM Platform to run on (default: ubuntu-latest)"
  echo "  -b, --bind              Bind working directory to act container"
  echo "  -v, --verbose           Enable verbose output"
  echo "  -h, --help              Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 -w .github/workflows/ci.yml"
  echo "  $0 -w .github/workflows/ci.yml -e pull_request"
  echo "  $0 -w .github/workflows/ci.yml -j build"
  echo ""
  echo "Note: This script assumes act is installed and Docker is running."
}

# Default values
WORKFLOW_FILE=""
EVENT_TYPE="push"
JOB_FILTER=""
PLATFORM="ubuntu-latest"
BIND_OPTION=""
VERBOSE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -w|--workflow)
      WORKFLOW_FILE="$2"
      shift 2
      ;;
    -e|--event)
      EVENT_TYPE="$2"
      shift 2
      ;;
    -j|--job)
      JOB_FILTER="$2"
      shift 2
      ;;
    -p|--platform)
      PLATFORM="$2"
      shift 2
      ;;
    -b|--bind)
      BIND_OPTION="--bind"
      shift
      ;;
    -v|--verbose)
      VERBOSE="--verbose"
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Validate required parameters
if [ -z "$WORKFLOW_FILE" ]; then
  echo "Error: Workflow file is required"
  show_help
  exit 1
fi

# Check if act is installed
if ! command -v act &> /dev/null; then
  echo "Error: act is not installed. Please install it first:"
  echo "https://github.com/nektos/act#installation"
  exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
  echo "Error: Docker is not running. Please start Docker Desktop and try again."
  exit 1
fi

# Create events directory if it doesn't exist
mkdir -p .github/events

# Create event file if it doesn't exist
EVENT_FILE=".github/events/$EVENT_TYPE.json"
if [ ! -f "$EVENT_FILE" ]; then
  TEMPLATE_FILE=".github/events/templates/$EVENT_TYPE.json"

  # Check if we have a template for this event type
  if [ -f "$TEMPLATE_FILE" ]; then
    echo "Creating $EVENT_TYPE event from template..."
    cp "$TEMPLATE_FILE" "$EVENT_FILE"
  else
    echo "Creating basic $EVENT_TYPE event..."
    echo '{
      "event_type": "'$EVENT_TYPE'"
    }' > "$EVENT_FILE"

    # If this is a pull_request event, warn about using the template
    if [ "$EVENT_TYPE" = "pull_request" ]; then
      echo "Warning: Pull request events require detailed context."
      echo "Consider using the provided template by running:"
      echo "cp .github/events/templates/pull_request.json .github/events/pull_request.json"
    fi
  fi
fi

# Build the command
CMD="act"

# Add workflow file
CMD="$CMD -W $WORKFLOW_FILE"

# Add event file
CMD="$CMD -e $EVENT_FILE"

# Add job filter if provided
if [ -n "$JOB_FILTER" ]; then
  CMD="$CMD --job $JOB_FILTER"
fi

# Add platform mappings
CMD="$CMD -P $PLATFORM=ghcr.io/catthehacker/ubuntu:act-latest"

# Add bind option if specified
if [ -n "$BIND_OPTION" ]; then
  CMD="$CMD $BIND_OPTION"
fi

# Add verbose option if specified
if [ -n "$VERBOSE" ]; then
  CMD="$CMD $VERBOSE"
fi

# Set environment variables for local testing
CMD="$CMD --env ACT=true"
CMD="$CMD --env ACT_LOCAL_TESTING=true"
CMD="$CMD --env GITHUB_TOKEN=local-testing-token"
CMD="$CMD -s GITHUB_TOKEN=local-testing-token"

# Display the command
echo "Running: $CMD"
echo "-----------------------------------"

# Run the command
eval $CMD

# Display completion message
echo "-----------------------------------"
echo "Local testing completed!"
