#!/bin/bash
# DEPRECATED: This script is deprecated in favor of using Hatch for running tests.
# Please use `hatch run test:cov` instead.
#
# This script is kept for backward compatibility but will be removed in a future version.
#

# Clean up any existing coverage data
rm -f .coverage
rm -f .coverage.*
rm -f coverage.xml
rm -rf htmlcov

# Run pytest with coverage for the conda_forge_converter package, explicitly specifying test files
pytest --cov=conda_forge_converter --cov-report=term-missing --cov-report=xml \
  tests/test_caching.py \
  tests/test_cli.py \
  tests/test_cli_performance.py \
  tests/test_core.py \
  tests/test_health.py \
  tests/test_incremental.py \
  tests/test_integration.py \
  tests/test_main.py \
  tests/test_ownership.py \
  tests/test_performance_improvements.py \
  tests/test_reporting.py \
  tests/test_utils.py \
  tests/test_validation.py \
  tests/test_version.py \
  tests/test_vscode_setup.py \
  "$@"
