#!/bin/bash
# Script to demonstrate local testing of act-compatible GitHub Actions workflows

# Ensure we're in the project root directory
cd "$(dirname "$0")"

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

# Display header
echo "====================================="
echo "Act-Compatible Workflow Testing Demo"
echo "====================================="
echo ""

# Test the sample workflow
echo "Testing sample-local-testing.yml workflow..."
echo "-----------------------------------"
act -W .github/workflows/sample-local-testing.yml -e .github/local-testing/events/push.json
echo ""

# Test the CI workflow
echo "Testing ci.yml workflow..."
echo "-----------------------------------"
act -W .github/workflows/ci.yml -e .github/local-testing/events/push.json --env ACT_LOCAL_TESTING=true
echo ""

echo "====================================="
echo "Act-compatible testing demo completed!"
echo "====================================="
echo ""
echo "For local testing, workflows should:"
echo "1. Use the ACT_LOCAL_TESTING environment variable to adapt behavior"
echo "2. Simplify matrix configurations when running locally"
echo "3. Skip steps that won't work in local testing"
echo ""
echo "For more options, see the documentation in github-actions-guide.md"
