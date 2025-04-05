# Conda-Forge Converter

A simple tool to convert Anaconda environments to conda-forge environments while preserving package versions.

[![Documentation](https://img.shields.io/badge/docs-latest-blue)](https://conda-forge-converter.readthedocs.io)
[![Tests](https://github.com/yourusername/conda-forge-converter/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/conda-forge-converter/actions/workflows/tests.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Quick Start

```bash
# Install
pip install conda-forge-converter

# Convert a single environment
conda-forge-converter -s myenv -t myenv_forge

# Batch convert with pattern matching
conda-forge-converter --batch --pattern 'data*'
```

## Key Features

- 🔄 Seamless Anaconda to conda-forge conversion
- 📦 Version-preserving package migration
- 🔍 Smart dependency resolution
- 🚀 Batch processing support
- ✅ Environment health verification

## Documentation

- [User Guide](https://conda-forge-converter.readthedocs.io/en/latest/user/)
- [CLI Reference](https://conda-forge-converter.readthedocs.io/en/latest/user/cli-reference.html)
- [Contributing](CONTRIBUTING.md)

## Development

```bash
# Install development tools
pipx install uv
pipx install pre-commit

# Setup development environment
./scripts/setup_dev.sh

# Update dependencies
python3 scripts/update_deps.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
