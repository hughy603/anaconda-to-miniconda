# Test Coverage Guide

> **Note:** This guide has been simplified. For comprehensive information about testing, see the [Testing section in the README.md](README.md#testing).

## Quick Reference

```bash
# Run tests with coverage
./run-tests.sh

# Run with verbose output
./run-tests.sh -v

# Run specific tests
./run-tests.sh -k "test_core"
```

## Coverage Configuration

The coverage configuration is defined in `pyproject.toml` with a minimum threshold of 60%.

## Improving Coverage

To improve the current coverage (around 47%):

1. Focus on writing tests for modules with low coverage
1. Add tests for missing code paths in partially covered modules
1. Consider excluding difficult-to-test code paths with `# pragma: no cover`
