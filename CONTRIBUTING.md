# Contributing to conda-forge-converter

Thank you for considering contributing to conda-forge-converter! This document provides guidelines and instructions for contributing.

## Development Environment

We recommend using hatch to set up your development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Set up development environment using hatch
hatch env create
```

Alternatively, you can use uv:

```bash
# Clone the repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e ".[dev]"
```

## Running Tests

We use pytest for testing:

```bash
# Using hatch
hatch run test

# Using pytest directly
pytest
```

## Code Style

We use black, isort, and ruff for code formatting and linting:

```bash
# Format code with hatch
hatch run lint:fmt

# Or manually
black src tests
isort src tests
ruff src tests
```

## Submitting Changes

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests (`hatch run test`)
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Create a new Pull Request

## Pull Request Process

1. Update the README.md with details of your changes if applicable
2. Make sure all tests pass
3. Update documentation if necessary
4. The PR will be merged once it receives approval from maintainers

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We strive to maintain a welcoming and inclusive environment for everyone.

## Questions?

Feel free to open an issue if you have any questions or need clarification on any aspect of the contribution process.