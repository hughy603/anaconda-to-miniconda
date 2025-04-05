# Contributing Guide

Thank you for considering contributing to Conda-Forge Converter! This document provides detailed guidelines for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We strive to maintain a welcoming and inclusive environment for everyone.

## Development Environment Setup

### Prerequisites

- Python 3.11 or later
- Git
- Conda or Miniconda (for testing)

### Setup Options

We support multiple methods for setting up the development environment:

#### Using hatch (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Set up development environment using hatch
pip install hatch
hatch env create
```

#### Using uv (Alternative)

```bash
# Clone the repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Create and activate a virtual environment
pip install uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e ".[dev]"
```

#### Using pip and venv (Alternative)

```bash
# Clone the repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Code Standards

We use several tools to ensure code quality:

### Formatting

- **black**: For code formatting
- **isort**: For import sorting

Format your code with:

```bash
# Using hatch
hatch run lint:fmt

# Using pre-commit
pre-commit run --all-files

# Manually
black src tests
isort src tests
```

### Linting

- **ruff**: For comprehensive Python linting
- **pyright**: For type checking

Run linting with:

```bash
# Using hatch
hatch run lint:check

# Using pre-commit
pre-commit run --all-files

# Manually
ruff src tests
pyright src tests
```

### Type Checking

We use Python's type annotations throughout the codebase:

```python
def add_numbers(a: int, b: int) -> int:
    return a + b
```

Run type checking with:

```bash
pyright src tests
```

## Testing

We use pytest for testing. Tests are organized in the `tests/` directory:

```
tests/
├── unit/             # Unit tests
│   ├── test_core.py
│   ├── test_cli.py
│   └── ...
├── integration/      # Integration tests
│   ├── test_conversion.py
│   └── ...
└── conftest.py       # Shared test fixtures
```

### Running Tests

```bash
# Using hatch
hatch run test

# Using pytest directly
pytest

# Run with coverage
pytest --cov=src

# Run a specific test file
pytest tests/unit/test_core.py

# Run a specific test
pytest tests/unit/test_core.py::test_environment_discovery
```

### Writing Tests

- Each module should have corresponding test modules
- Use pytest fixtures for shared resources
- Aim for at least 80% code coverage
- Use parametrization for testing multiple scenarios

Example test:

```python
import pytest
from conda_forge_converter.core import extract_packages


def test_extract_packages():
    # Test setup
    env_data = {...}

    # Call function
    result = extract_packages(env_data)

    # Assert expectations
    assert "numpy" in result
    assert result["numpy"] == "1.22.4"
```

## Branching Strategy

We follow a modified GitFlow branching strategy:

- `main`: Latest stable release
- `develop`: Latest development changes
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `release/*`: Release preparation

## Pull Request Process

1. Create a feature branch from `develop`:

   ```bash
   git checkout develop
   git pull
   git checkout -b feature/your-feature-name
   ```

1. Make your changes, adhering to code standards

1. Update documentation and tests

1. Commit your changes with descriptive messages:

   ```bash
   git commit -m "Add feature X to solve problem Y"
   ```

1. Push your branch and create a pull request:

   ```bash
   git push origin feature/your-feature-name
   ```

1. GitHub will provide a link to create the PR, or you can create it from the GitHub UI

### PR Requirements

- All tests must pass
- Code must be formatted and linted
- Type checking must pass
- Documentation must be updated
- Unit tests must be added for new features
- Existing test coverage should not decrease

## Documentation

We use Markdown for documentation. All changes should include appropriate documentation updates:

- **Code Documentation**: Docstrings for public APIs
- **README**: Update for new features or changes
- **User Guides**: In `docs/user/`
- **Developer Guides**: In `docs/dev/`
- **API Documentation**: In `docs/api/`

### Docstring Style

We follow the Google style for docstrings:

```python
def function_with_pep484_type_annotations(param1: int, param2: str) -> bool:
    """Example function with PEP 484 type annotations.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.

    Raises:
        ValueError: If param1 is negative.
    """
    if param1 < 0:
        raise ValueError("param1 must be positive")
    return param1 > len(param2)
```

## Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Added functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

## Release Process

1. Create a release branch:

   ```bash
   git checkout develop
   git pull
   git checkout -b release/vX.Y.Z
   ```

1. Update version information and finalize documentation

1. Submit a PR to merge into `main`

1. After approval, tag the release:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

1. GitHub Actions will automatically build and publish the package

## Getting Help

If you need help with contributing:

- Check existing issues and pull requests
- Join our community channels
- Open a new issue with the "question" label

## Thank You!

Your contributions are what make the open-source community amazing. Thank you for taking the time to contribute!
