# Testing Documentation

This directory contains tests for the conda-forge-converter and github-actions-validator packages.

## Test Structure

- Unit tests: Tests for individual components
- Integration tests: Tests that verify multiple components working together
- Benchmark tests: Performance tests (excluded from regular test runs)

## Running Tests

The project uses pytest for testing. Tests can be run using the following commands:

```bash
# Run all tests with coverage
python -m pytest

# Run only unit tests
python -m pytest -m "unit"

# Run only integration tests
python -m pytest -m "integration"

# Run specific test files
python -m pytest tests/test_github_actions_validator.py

# Run tests excluding slow and integration tests
python -m pytest -k "not slow and not integration"

# Run tests with verbose output
python -m pytest -v
```

Alternatively, you can use the predefined scripts in pyproject.toml:

```bash
# Using hatch
hatch run test
hatch run test-unit
hatch run test-integration
hatch run test-github-actions
hatch run test-conda-forge
hatch run test-fast
```

## Coverage

Code coverage is automatically measured when running tests. The configuration is in `.coveragerc` and the minimum required coverage is 8%.

To view the coverage report:

- Terminal output is shown after test runs
- HTML report is generated in the `htmlcov` directory
- XML report is generated as `coverage.xml`

To clean coverage data:

```bash
hatch run clean-coverage
```

### Improving Coverage

The project includes a script to help gradually increase the coverage threshold over time:

```bash
# Using the script directly
python scripts/update_coverage_threshold.py

# Using hatch
hatch run update-coverage-threshold

# Update the coverage threshold by a custom percentage
python scripts/update_coverage_threshold.py --increment 2.5
```

This script reads the current coverage from the coverage.xml file and updates the fail_under threshold in .coveragerc to a slightly higher value, encouraging continuous improvement.

## Test Configuration

- `pytest.ini`: Contains pytest configuration
- `.coveragerc`: Contains coverage configuration

## Adding New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py` for files, `Test*` for classes, and `test_*` for functions
1. Use appropriate markers for categorization (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)
1. Keep unit tests fast and focused on a single component
1. Use mocks for external dependencies in unit tests
