# Dependency Management

This project uses modern Python dependency management tools to ensure reproducible builds and development environments.

## Tools

- **uv**: A fast Python package installer and resolver (v0.6.12+)
- **pyproject.toml**: Single source of truth for dependencies
- **pre-commit**: Automated checks including dependency locking
- **hatch**: Project management tool

## Setup

To set up the development environment:

```bash
# Install required tools
pipx install uv
pipx install pre-commit

# Run the setup script
./scripts/setup_dev.sh
```

## Dependency Management Workflow

### Define dependencies in pyproject.toml

- Regular dependencies under `project.dependencies`
- Development dependencies under `project.optional-dependencies.dev`
- Test dependencies under `project.optional-dependencies.test`

### Lock dependencies

- Dependencies are locked automatically via pre-commit hooks
- Alternatively, run `python3 scripts/update_deps.py` manually

### Generated files

- `requirements/requirements.txt`: Production dependencies
- `requirements/dev-requirements.txt`: Development dependencies
- `requirements/test-requirements.txt`: Test dependencies
- `requirements/ci-requirements.txt`: Combined dev and test for CI

## Resolution Strategy

This project uses the `highest` resolution strategy in uv, which resolves dependencies to their highest compatible
versions available. This ensures we always use the latest compatible versions while maintaining stability.

## CI/CD Integration

For CI/CD pipelines, use the locked requirements files:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: |
    pip install -r requirements/ci-requirements.txt
```

## Upgrading Dependencies

To upgrade dependencies:

1. Update versions in `pyproject.toml`
1. Run `python3 scripts/update_deps.py` to regenerate lock files
1. Test the changes with `pre-commit run --all-files`

## Best Practices

- Never modify the generated requirements files directly
- Always specify version constraints in `pyproject.toml`
- Use `uv pip install -e ".[dev,test]"` for local development
- Run tests after dependency updates to verify compatibility
- Keep uv updated to the latest stable version
