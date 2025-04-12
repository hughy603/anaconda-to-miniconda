# Conda-Forge Converter

A simple tool to convert Anaconda environments to conda-forge environments while preserving package versions.

[![Documentation](https://img.shields.io/badge/docs-latest-blue)](https://conda-forge-converter.readthedocs.io)
[![CI](https://github.com/yourusername/conda-forge-converter/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/conda-forge-converter/actions/workflows/ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Release](https://github.com/yourusername/conda-forge-converter/actions/workflows/release.yml/badge.svg)](https://github.com/yourusername/conda-forge-converter/actions/workflows/release.yml)
[![Maintenance](https://github.com/yourusername/conda-forge-converter/actions/workflows/maintenance.yml/badge.svg)](https://github.com/yourusername/conda-forge-converter/actions/workflows/maintenance.yml)
[![Code Coverage](https://codecov.io/gh/yourusername/conda-forge-converter/branch/master/graph/badge.svg)](https://codecov.io/gh/yourusername/conda-forge-converter)
[![PyPI version](https://badge.fury.io/py/conda-forge-converter.svg)](https://badge.fury.io/py/conda-forge-converter)
[![Python Versions](https://img.shields.io/pypi/pyversions/conda-forge-converter.svg)](https://pypi.org/project/conda-forge-converter/)
[![License](https://img.shields.io/github/license/yourusername/conda-forge-converter.svg)](https://github.com/yourusername/conda-forge-converter/blob/master/LICENSE)

## Quick Start

```bash
# Install with UV (recommended)
uv pip install conda-forge-converter

# Or with pipx for isolated installation
pipx install conda-forge-converter

# Convert and replace a single environment (original is backed up as myenv_anaconda_backup)
conda-forge-converter -s myenv

# Convert to a new environment without replacing the original
conda-forge-converter -s myenv --no-replace -t myenv_forge

# Batch convert with pattern matching (replaces all matching environments)
conda-forge-converter --batch --pattern 'data*'

# Batch convert without replacing original environments
conda-forge-converter --batch --pattern 'data*' --no-replace
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
- [Dependency Management](DEPENDENCY_MANAGEMENT.md)

## Development

> **⚠️ IMPORTANT:** Always use UV for all package installations (`uv pip install`) instead of regular pip. Using regular pip can lead to dependency conflicts and test failures. See [Dependency Management](DEPENDENCY_MANAGEMENT.md) for details.

```bash
# Install UV (recommended to use pipx for global installation)
pipx install uv
pipx install pre-commit

# Setup development environment
uv pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install

# Lock dependencies
uv run deps-lock

# Run tests
uv run test

# Run tests with coverage
uv run test-cov

# Run linting and formatting
uv run lint
uv run format

# Run type checking
uv run type-check

# Run security checks
uv run security

# Build documentation
hatch run docs-build

# Serve documentation locally
hatch run docs-serve

# Set up VSCode configuration
./scripts/setup_vscode.py

# Test GitHub Actions workflows locally
.github/local-testing/test-workflow.sh .github/workflows/ci.yml

# Initialize gh-pages branch for benchmarks (one-time setup)
# Run this workflow from GitHub Actions UI before running benchmarks
# Go to Actions -> Initialize gh-pages Branch -> Run workflow -> Type "yes" to confirm
```

### Performance Benchmarks

This project includes performance benchmarking to track code efficiency over time:

1. **Setup**: Before running benchmarks for the first time, you need to initialize the gh-pages branch:

   - Go to GitHub Actions -> "Initialize gh-pages Branch" workflow
   - Click "Run workflow"
   - Type "yes" to confirm and run the workflow

1. **Running Benchmarks**:

   - Benchmarks run automatically on PRs and weekly
   - You can manually trigger the benchmark workflow from Actions tab
   - Results are published to GitHub Pages

1. **Viewing Results**:

   - Benchmark results are available at: <https://yourusername.github.io/conda-forge-converter/dev/bench/>
   - Performance regressions (>200%) will trigger alerts on PRs

### VSCode Integration

This project includes pre-configured VSCode settings to help you get started quickly:

1. **Automatic Setup**: Run `./scripts/setup_vscode.py` to set up VSCode configuration
1. **Debug Configurations**: Pre-configured launch configurations for debugging
1. **Tasks**: Common development tasks accessible via the VSCode Tasks menu
1. **Extensions**: Recommended extensions for Python development

For detailed information on debugging with VSCode, see [VSCode Debugging Guide](docs/dev/vscode-debugging.md).

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
