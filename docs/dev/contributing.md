# Contributing Guide

Thank you for considering contributing to Conda-Forge Converter! This document provides an overview of the contribution process. For more detailed information, please refer to the specific guides linked throughout this document.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We strive to maintain a welcoming and inclusive environment for everyone.

## Quick Start

For a complete guide to setting up your development environment and understanding the workflow, see the [Developer Workflow Guide](workflow.md) and [Development Setup Guide](setup.md).

```bash
# Clone the repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Install UV (recommended)
pipx install uv

# Set up development environment
uv pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

## Development Process Overview

1. **Set up your environment**: Follow the [Development Setup Guide](setup.md)
1. **Create a feature branch**: `git checkout -b feature/your-feature-name`
1. **Make your changes**: Implement your feature or bug fix
1. **Run tests and checks**: Use pre-commit hooks and pytest
1. **Commit your changes**: Follow the [Conventional Commits Guide](conventional-commits.md)
1. **Submit a pull request**: Follow the [Pull Request Process Guide](pr-process.md)

For detailed information about each step, please refer to the [Developer Workflow Guide](workflow.md).

## Code Standards

We use several tools to ensure code quality:

- **Ruff**: For linting and formatting
- **Pyright**: For type checking
- **Pre-commit**: For automated checks

For details on our code standards and tools, see the [Build Tools Guide](build-tools.md).

## Testing

We use pytest for testing. For detailed information about writing and running tests, see the [Testing Guide](testing.md).

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src
```

## Documentation

All changes should include appropriate documentation updates. For information about our documentation standards and process, see the [Documentation Guide](documentation.md) and [Documentation Contribution Guide](doc-contributing.md).

## Versioning and Releases

We follow [Semantic Versioning](https://semver.org/). For detailed information about our release process, see the [Release Process Guide](releasing.md).

## Getting Help

If you need help with contributing:

- Check the [Quick Reference Guide](quick-reference.md) for common tasks and troubleshooting
- Check existing issues and pull requests
- Open a new issue with the "question" label

## Thank You!

Your contributions are what make the open-source community amazing. Thank you for taking the time to contribute!
