# Conda-Forge Converter

A simple tool to convert Anaconda environments to conda-forge environments while preserving package versions.

## Installation

```bash
pip install conda-forge-converter
```

## Basic Usage

Convert a single environment:

```bash
conda-forge-converter -s myenv -t myenv_forge
```

Convert all environments (adds "\_forge" suffix by default):

```bash
conda-forge-converter --batch
```

Specify Python version for the new environment:

```bash
conda-forge-converter -s myenv -t myenv_forge --python 3.11
```

Preview without creating:

```bash
conda-forge-converter -s myenv -t myenv_forge --dry-run
```

## Additional Options

Convert environments matching a pattern:

```bash
conda-forge-converter --batch --pattern 'data*'
```

Exclude specific environments:

```bash
conda-forge-converter --batch --exclude 'test_env,dev_env'
```

Check environment health:

```bash
conda-forge-converter health myenv
```

For all options:

```bash
conda-forge-converter --help
```

## Dependency Management

This project uses a modern dependency management approach based on [uv](https://github.com/astral-sh/uv) and pre-commit hooks.

Key components:

- **pyproject.toml**: Source of truth for all dependencies
- **uv**: Fast Python package installer used for dependency resolution
- **pre-commit**: Automated checks and dependency locking

For detailed information about the dependency management strategy, see [DEPENDENCY_MANAGEMENT.md](DEPENDENCY_MANAGEMENT.md).

## Quick Setup

```bash
# Install tools
pipx install uv
pipx install pre-commit

# Set up development environment
./scripts/setup_dev.sh

# Manual dependency update
python3 scripts/update_deps.py
```
