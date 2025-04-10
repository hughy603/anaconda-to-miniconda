#!/bin/bash
# This script runs a subset of tests quickly for development purposes

# Clean up any existing coverage data
rm -f .coverage
rm -f .coverage.*
rm -f coverage.xml
rm -rf htmlcov

# Default to running cli tests if no arguments provided
if [ $# -eq 0 ]; then
  TEST_FILES="tests/test_cli.py"
else
  TEST_FILES="$@"
fi

echo "Running fast tests on: $TEST_FILES"

# Run pytest with coverage for the specified test files
# But don't fail on coverage thresholds since we're only running a subset of tests
pytest --cov=conda_forge_converter --cov-report=term-missing \
  --cov-fail-under=0 \
  $TEST_FILES
