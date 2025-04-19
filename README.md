# Conda-Forge Converter

A tool to convert Anaconda environments to conda-forge environments while preserving package versions.

[![CI](https://github.com/yourusername/conda-forge-converter/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/conda-forge-converter/actions/workflows/ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![PyPI version](https://badge.fury.io/py/conda-forge-converter.svg)](https://badge.fury.io/py/conda-forge-converter)
[![Python Versions](https://img.shields.io/pypi/pyversions/conda-forge-converter.svg)](https://pypi.org/project/conda-forge-converter/)
[![License](https://img.shields.io/github/license/yourusername/conda-forge-converter.svg)](https://github.com/yourusername/conda-forge-converter/blob/master/LICENSE)

## Table of Contents

- [Conda-Forge Converter](#conda-forge-converter)
  - [Table of Contents](#table-of-contents)
  - [Quick Start](#quick-start)
  - [Features](#features)
  - [Advanced Usage](#advanced-usage)
    - [Specify Channels](#specify-channels)
    - [Control Package Handling](#control-package-handling)
    - [Validation Options](#validation-options)
  - [Development Setup](#development-setup)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Dependency Management](#dependency-management)
    - [Key Rules](#key-rules)
    - [Common Commands](#common-commands)
  - [Testing](#testing)
  - [GitHub Actions](#github-actions)
    - [GitHub Actions Workflow Validation](#github-actions-workflow-validation)
      - [Key Features](#key-features)
    - [Local Workflow Testing](#local-workflow-testing)
  - [Project Structure](#project-structure)
  - [License](#license)

## Quick Start

```bash
# Install with UV (recommended)
uv pip install conda-forge-converter

# Or with pipx for isolated installation
pipx install conda-forge-converter

# Convert and replace a single environment (original is backed up)
conda-forge-converter -s myenv

# Convert to a new environment without replacing the original
conda-forge-converter -s myenv --no-replace -t myenv_forge

# Batch convert with pattern matching
conda-forge-converter --batch --pattern 'data*'
```

## Features

- 🔄 Seamless Anaconda to conda-forge conversion
- 📦 Version-preserving package migration
- 🔍 Smart dependency resolution
- 🚀 Batch processing support
- ✅ Environment health verification

## Advanced Usage

### Specify Channels

```bash
# Specify additional channels to include
conda-forge-converter -s myenv --channels conda-forge,bioconda
```

### Control Package Handling

```bash
# Skip specific packages
conda-forge-converter -s myenv --skip-packages numpy,pandas

# Force specific package versions
conda-forge-converter -s myenv --force-versions scipy=1.7.0
```

### Validation Options

```bash
# Run validation after conversion
conda-forge-converter -s myenv --validate

# Skip validation
conda-forge-converter -s myenv --no-validate
```

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- Docker Desktop (for workflow testing)

### Installation

```bash
# Install required tools
pipx install uv
pipx install pre-commit

# Clone and set up the project
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Install dependencies
uv pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

## Dependency Management

This project uses modern Python dependency management tools:

- **UV**: Fast Python package installer and resolver
- **Hatch**: Build system and packaging tool
- **pyproject.toml**: Single source of truth for dependencies

### Key Rules

- Always use UV for package installations (`uv pip install`)
- Never use regular `pip install` as it bypasses the dependency management system
- Add dependencies to `pyproject.toml` under the appropriate section
- Use `uv run deps-lock` to update the lock file after changing dependencies

### Common Commands

```bash
# Lock dependencies
uv run deps-lock

# Update dependencies
uv run deps-update

# Install from lock file
uv pip install -r requirements.lock
```

## Testing

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

Note: Pre-commit hooks only run fast tests. To run all tests before committing, use:

```bash
# Run all tests with coverage
pytest --cov=src
```

## GitHub Actions

### GitHub Actions Workflow Validation

This project includes comprehensive tools for validating GitHub Actions workflows locally:

```bash
# Validate all workflows
./validate-all-workflows.sh  # Unix/Linux/macOS
.\validate-all-workflows.ps1  # Windows

# Validate only changed workflows
./validate-all-workflows.sh --changed-only
.\validate-all-workflows.ps1 -ChangedOnly

# Fast validation (dry run mode)
./validate-all-workflows.sh --dry-run
.\validate-all-workflows.ps1 -DryRun
```

#### Key Features

- **Syntax Validation**: Check for errors and best practices
- **Execution Validation**: Run workflows in local containers
- **Selective Testing**: Validate only changed workflows
- **Parallel Execution**: Run validations concurrently
- **Mock Secrets**: Use local secrets for testing
- **Custom Docker Images**: More accurate testing environment
- **VSCode Integration**: Convenient tasks for validation
- **Pre-commit Integration**: Automatic validation on commit

For detailed information, see [GitHub Actions Validation](GITHUB_ACTIONS_VALIDATION.md).

### Local Workflow Testing

Test individual GitHub Actions workflows locally:

```bash
# Unix/Linux/macOS
./github-actions-local.sh -w .github/workflows/ci.yml  # Test a workflow
./github-actions-local.sh -w .github/workflows/ci.yml -j build  # Test specific job
./github-actions-local.sh -w .github/workflows/ci.yml -e pull_request  # Test event type

# Windows (PowerShell)
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -JobFilter build
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request
```

For detailed information about workflow validation, local testing, and troubleshooting, see [GitHub Actions Validation](GITHUB_ACTIONS_VALIDATION.md).

## Project Structure

```
conda-forge-converter/
├── src/                  # Source code
├── tests/                # Test suite
├── docs/                 # Documentation
├── examples/             # Example scripts
├── scripts/              # Utility scripts
├── pyproject.toml        # Project configuration
├── requirements.lock     # Locked dependencies
└── .github/workflows/    # CI/CD pipelines
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Test comment

# Test comment

# Test comment

# Another test comment

# Another test comment

# Another test comment

# Test comment for debugging
# Test comment for debugging
