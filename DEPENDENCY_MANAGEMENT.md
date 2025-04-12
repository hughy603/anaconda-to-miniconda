# Dependency Management

> **Note:** This guide has been simplified. For comprehensive information, see the [Dependency Management section in the README.md](README.md#dependency-management).

## Key Rules

- Always use UV for package installations (`uv pip install`)
- Never use regular `pip install` as it bypasses the dependency management system
- Add dependencies to `pyproject.toml` under the appropriate section
- Use `uv run deps-lock` to update the lock file after changing dependencies

## Quick Reference

```bash
# Install dependencies
uv pip install -e ".[dev,test]"

# Lock dependencies
uv run deps-lock

# Update dependencies
uv run deps-update

# Install from lock file
uv pip install -r requirements.lock
```

## Helper Script

Use the helper script to ensure UV is always used for package installation:

```bash
# Install a package with UV
python scripts/install_package.py package_name

# Install multiple packages
python scripts/install_package.py package1 package2

# Install development dependencies
python scripts/install_package.py -e --dev
```

## Common Issues

If you encounter missing dependencies when running tests with Hatch:

1. Add the dependency to `pyproject.toml` under the appropriate section
1. Run `uv pip install -e ".[dev,test]"` to update your environment
