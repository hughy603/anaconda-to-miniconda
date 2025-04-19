# Testing Guide

## Test Categories

- **Fast tests**: Default tests that run quickly (excludes slow and integration tests)
- **Integration tests**: Tests that interact with external systems
- **Slow tests**: Tests that take longer to run

## Running Tests

```bash
# Run all tests
pytest

# Run fast tests only (skips slow and integration tests)
pytest -k "not slow and not integration"

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m slow

# Run tests for a specific file
pytest tests/test_specific_file.py
```

## Pre-commit and Pre-push Hooks

- Pre-commit hooks only run fast tests: `pytest -k "not slow and not integration"`
- To run all tests before pushing, uncomment the pytest line in the pre-push hook
