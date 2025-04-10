# Test Coverage Guide

This document explains how to run tests with coverage for the conda-forge-converter project.

## Running Tests with Coverage

We've created a shell script to run tests with coverage. The script handles cleaning up previous coverage data and running pytest with the correct coverage configuration.

### Using the Shell Script

To run tests with coverage, use the `run-tests.sh` script:

```bash
./run-tests.sh
```

This will:

1. Clean up any existing coverage data
1. Run pytest with coverage for the conda_forge_converter package
1. Generate a coverage report in the terminal and an XML report for CI integration

### Additional Options

You can pass additional pytest arguments to the script:

```bash
./run-tests.sh -v  # Run with verbose output
./run-tests.sh -k "test_core"  # Run only tests with "test_core" in their name
```

## Coverage Configuration

The coverage configuration is defined in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["conda_forge_converter"]
branch = false

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "pass",
    "raise ImportError"
]
fail_under = 60
show_missing = true
```

## UV Integration Note

The project previously used UV's scripts feature for running tests with coverage, but this feature is not supported in the current version of UV. The `run-tests.sh` script provides a reliable alternative.

## Improving Coverage

The current coverage is around 21%, which is below our required threshold of 60%. To improve coverage:
The current coverage is around 47%, which is below the ideal threshold of 80%. To improve coverage:

1. Focus on writing tests for modules with low coverage (e.g., `cleanup.py`, `progress.py`)
1. Add tests for missing code paths in partially covered modules
1. Consider excluding certain code paths that are difficult to test (using `# pragma: no cover`)
