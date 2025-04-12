# Conda-Forge Converter

A tool to convert Anaconda environments to conda-forge environments while preserving package versions.

[![CI](https://github.com/yourusername/conda-forge-converter/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/conda-forge-converter/actions/workflows/ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![PyPI version](https://badge.fury.io/py/conda-forge-converter.svg)](https://badge.fury.io/py/conda-forge-converter)
[![Python Versions](https://img.shields.io/pypi/pyversions/conda-forge-converter.svg)](https://pypi.org/project/conda-forge-converter/)
[![License](https://img.shields.io/github/license/yourusername/conda-forge-converter.svg)](https://github.com/yourusername/conda-forge-converter/blob/master/LICENSE)

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Advanced Usage](#advanced-usage)
- [Development Setup](#development-setup)
- [Dependency Management](#dependency-management)
- [Testing](#testing)
- [GitHub Actions](#github-actions)
- [Project Structure](#project-structure)

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
hatch run test

# Run with coverage
hatch run test-cov

# Run linting
hatch run lint

# Run type checking
hatch run type-check

# Run security checks
hatch run security
```

## GitHub Actions

### Local Workflow Testing

Test GitHub Actions workflows locally before pushing changes using our standardized scripts:

```bash
# Test a workflow (defaults to push event)
./github-actions-local.sh -w .github/workflows/ci.yml

# Test with a specific job
./github-actions-local.sh -w .github/workflows/ci.yml -j build

# Test with a different event type
./github-actions-local.sh -w .github/workflows/ci.yml -e pull_request
```

For Windows users (PowerShell):

```powershell
# Test a workflow
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml

# Test a specific job
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -JobFilter build

# Test with a different event type
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request
```

For detailed information about local testing, see [GITHUB_ACTIONS_LOCAL.md](GITHUB_ACTIONS_LOCAL.md).

### Environment Variables for Local Testing

The following environment variables are automatically set during local testing:

| Variable                  | Value  | Purpose                                     |
| ------------------------- | ------ | ------------------------------------------- |
| `ACT`                     | `true` | Identify when running in act                |
| `ACT_LOCAL_TESTING`       | `true` | Identify when running in local testing mode |
| `SKIP_LONG_RUNNING_TESTS` | `true` | Skip long-running tests in local testing    |

### Troubleshooting Workflow Issues

1. **Docker not running**

   - Start Docker Desktop and try again

1. **"Unknown action" error**

   - For composite actions, use relative paths: `./.github/actions/my-action`
   - Some third-party actions may not be compatible with Act

1. **Tests pass locally but fail in CI**

   - Check for environment differences
   - Ensure dependencies are properly specified

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
