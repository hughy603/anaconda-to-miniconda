# Dependency Management

This project uses modern Python dependency management tools to ensure reproducible builds and development environments.

> **Note:** For a more comprehensive guide to our build and dependency management tools, please refer to the [Build Tools Guide](docs/dev/build-tools.md).

## Tools

- **UV**: A fast Python package installer and resolver (v0.6.12+)
- **Hatch**: Build system and packaging tool
- **pyproject.toml**: Single source of truth for dependencies
- **pre-commit**: Automated checks including dependency locking

## Quick Reference

### Setup

```bash
# Install required tools
pipx install uv
pipx install pre-commit

# Install dependencies
uv pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

### Common Commands

```bash
# Lock dependencies
uv run deps-lock

# Update dependencies
uv run deps-update

# Install from lock file
uv pip install -r requirements.lock

# Run tests with Hatch
hatch run test:run

# Run tests with coverage
hatch run test
```

### Dependency Structure

- Regular dependencies under `project.dependencies`
- Development dependencies under `project.optional-dependencies.dev`
- Test dependencies under `project.optional-dependencies.test`

## Best Practices

- Never modify the generated requirements.lock file directly
- Always specify version constraints in `pyproject.toml`
- Use `uv pip install -e ".[dev,test]"` for local development
- Use Hatch for running tests: `hatch run test`
- Run tests after dependency updates to verify compatibility
- Keep UV updated to the latest stable version

For detailed information about dependency management, including resolution strategy, CI/CD integration, and automated updates, please refer to the [Build Tools Guide](docs/dev/build-tools.md).
