#!/bin/bash
# Script to demonstrate local testing of GitHub Actions workflows

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
echo "GitHub Actions Local Testing Demo"
echo "====================================="
echo ""

# Test the sample workflow
echo "Testing sample-local-testing.yml workflow..."
echo "-----------------------------------"
.github/local-testing/local-test.sh .github/workflows/sample-local-testing.yml
echo ""

# Test the CI workflow with Python 3.11
echo "Testing CI workflow with Python 3.11..."
echo "-----------------------------------"
.github/local-testing/local-test.sh .github/workflows/ci.yml push "" python-version=3.11
echo ""

# Validate a workflow
echo "Validating sample workflow..."
echo "-----------------------------------"
.github/local-testing/validate-workflow.sh .github/workflows/sample-local-testing.yml
echo ""

# Validate CI workflow
echo "Validating CI workflow..."
echo "-----------------------------------"
.github/local-testing/validate-workflow.sh .github/workflows/ci.yml
echo ""

echo "====================================="
echo "Local testing demo completed!"
echo "====================================="
echo ""
echo "For more options, see the documentation in github-actions-guide.md"
