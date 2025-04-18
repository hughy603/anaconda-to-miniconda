# Contributing to GitHub Actions Validator

Thank you for your interest in contributing to the GitHub Actions Validator! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We expect all contributors to follow our Code of Conduct.

## Getting Started

1. Fork the repository
1. Clone your fork:
   ```bash
   git clone https://github.com/your-username/your-fork.git
   cd your-fork
   ```
1. Install the package in development mode:
   ```bash
   pip install -e .
   ```
1. Install development dependencies:
   ```bash
   pip install -e ".[dev,test]"
   ```
1. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
1. Make your changes
1. Run tests to ensure your changes don't break existing functionality:
   ```bash
   pytest
   ```
1. Run linters to ensure your code follows our style guidelines:
   ```bash
   ruff check .
   ruff format .
   ```
1. Commit your changes with a descriptive commit message:
   ```bash
   git commit -m "Add feature: your feature description"
   ```
1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
1. Create a pull request from your fork to the main repository

## Project Structure

The project is organized as follows:

```
src/github_actions_validator/
├── __init__.py           # Package initialization
├── _version.py           # Version information
├── cli.py                # Command-line interface
├── config.py             # Configuration handling
├── discovery.py          # Workflow discovery
├── error_handling.py     # Error handling and reporting
├── validators/           # Validation modules
│   ├── __init__.py
│   ├── syntax.py         # Syntax validation
│   └── execution.py      # Execution validation
├── runners/              # Runner modules
│   ├── __init__.py
│   └── act.py            # Act runner
├── docs/                 # Documentation
│   ├── matrix_jobs.md
│   └── troubleshooting.md
└── examples/             # Example scripts
    ├── validate_workflows.py
    └── pre-commit-hooks.yaml
```

## Adding New Features

When adding new features, please follow these guidelines:

1. **Maintain backward compatibility**: Ensure that existing functionality continues to work
1. **Add tests**: Write tests for your new feature
1. **Update documentation**: Update the relevant documentation
1. **Follow the coding style**: Use the same coding style as the rest of the project

## Common Tasks

### Adding a New Validator

To add a new validator:

1. Create a new file in the `validators` directory
1. Implement your validator function
1. Update the `validators/__init__.py` file to expose your validator
1. Add tests for your validator
1. Update the documentation

### Adding a New Runner

To add a new runner:

1. Create a new file in the `runners` directory
1. Implement your runner class
1. Update the `runners/__init__.py` file to expose your runner
1. Add tests for your runner
1. Update the documentation

### Improving Error Handling

To improve error handling:

1. Update the `error_handling.py` file
1. Add new error patterns and suggestions
1. Add tests for your changes
1. Update the documentation

## Testing

We use pytest for testing. To run the tests:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=github_actions_validator
```

## Documentation

We use Markdown for documentation. To update the documentation:

1. Edit the relevant Markdown files in the `docs` directory
1. If you're adding a new feature, consider adding a new documentation file

## Releasing

Releases are handled by the maintainers. If you think your changes warrant a new release, please mention this in your pull request.

## Getting Help

If you need help with contributing, please open an issue or reach out to the maintainers.

## Thank You

Thank you for contributing to the GitHub Actions Validator! Your contributions help make this project better for everyone.
