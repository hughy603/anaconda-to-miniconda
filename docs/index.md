# Conda-Forge Converter

A tool for converting Anaconda environments to conda-forge and validating GitHub Actions workflows.

## Features

- Convert Anaconda environments to conda-forge
- Validate GitHub Actions workflows
- Comprehensive test coverage
- Modern Python tooling and best practices

## Quick Start

```bash
# Install with pip
pip install conda-forge-converter

# Or install with uv (recommended)
uv pip install conda-forge-converter
```

For detailed installation instructions, see the [Installation Guide](user/getting-started.md).

## Project Status

[![CI](https://github.com/anaconda/anaconda-to-miniconda/actions/workflows/ci.yml/badge.svg)](https://github.com/anaconda/anaconda-to-miniconda/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/anaconda/anaconda-to-miniconda/branch/main/graph/badge.svg)](https://codecov.io/gh/anaconda/anaconda-to-miniconda)
[![Documentation](https://github.com/anaconda/anaconda-to-miniconda/actions/workflows/docs.yml/badge.svg)](https://anaconda.github.io/anaconda-to-miniconda/)
[![PyPI version](https://badge.fury.io/py/conda-forge-converter.svg)](https://badge.fury.io/py/conda-forge-converter)
[![License](https://img.shields.io/github/license/anaconda/anaconda-to-miniconda)](https://github.com/anaconda/anaconda-to-miniconda/blob/main/LICENSE)

## Architecture

```mermaid
graph TD
    A[User Input] --> B[CLI Interface]
    B --> C[Environment Parser]
    C --> D[Package Resolver]
    D --> E[Conda-Forge Converter]
    E --> F[Output Environment]
    B --> G[GitHub Actions Validator]
    G --> H[Workflow Parser]
    H --> I[Validation Rules]
    I --> J[Validation Report]
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](dev/contributing.md) for details.

## Key Features

- 🔄 Seamless conversion from Anaconda to conda-forge
- 📦 Preserves package versions and dependencies
- 🔍 Smart package resolution and compatibility checking
- 🚀 Batch processing with pattern matching
- ✅ Environment health verification
- 🔧 Support for both conda and pip packages

## Documentation Sections

### User Guide

- [Getting Started](user/getting-started.md)
- [CLI Reference](user/cli-reference.md)
- [Common Workflows](user/workflows.md)
- [Troubleshooting](user/troubleshooting.md)

### Developer Guide

- [Architecture](dev/architecture.md)
- [Contributing](dev/contributing.md)
- [Development Setup](dev/setup.md)
- [Testing](dev/testing.md)

### Design & Architecture

- [System Design](design/system-design.md)
- [Package Resolution](design/package-resolution.md)
- [Error Handling](design/error-handling.md)

## Why Use conda-forge?

- 🏢 Community-maintained packages
- 🔄 More up-to-date package versions
- 🧩 Better dependency resolution
- 📚 Broader package selection
- 🛠️ Active maintenance and support

See our [TODO list](TODO.md) for current development status and planned features.
