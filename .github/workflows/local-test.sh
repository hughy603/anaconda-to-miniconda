#!/usr/bin/env bash
# Simple GitHub Actions Local Testing Script
# Uses act directly with minimal configuration

set -euo pipefail

# Default values
WORKFLOW_FILE=".github/workflows/ci.yml"
EVENT_TYPE="push"
JOB_FILTER=""

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
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -w, --workflow FILE  Workflow file to run (default: .github/workflows/ci.yml)"
            echo "  -e, --event TYPE     Event type (default: push)"
            echo "  -j, --job JOB        Run specific job"
            echo "  -h, --help           Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo "Error: act is not installed. Please install it first:"
    echo "https://github.com/nektos/act#installation"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Build the act command
CMD="act"

# Add workflow file
CMD="$CMD -W $WORKFLOW_FILE"

# Add event type
CMD="$CMD -e $EVENT_TYPE"

# Add job filter if provided
if [ -n "$JOB_FILTER" ]; then
    CMD="$CMD --job $JOB_FILTER"
fi

# Set environment variables for local testing
CMD="$CMD --env ACT=true"
CMD="$CMD --env ACT_LOCAL_TESTING=true"
CMD="$CMD --env GITHUB_TOKEN=local-testing-token"

# Run the command
echo "Running: $CMD"
eval "$CMD"
