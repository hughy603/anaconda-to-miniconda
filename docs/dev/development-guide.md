# Development Guide

This guide consolidates information from various documentation files to provide a comprehensive reference for developers.

## Dependency Management

### Key Rules

- Always use UV for package installations (`uv pip install`)
- Never use regular `pip install` as it bypasses the dependency management system
- Add dependencies to `pyproject.toml` under the appropriate section
- Use `uv run deps-lock` to update the lock file after changing dependencies

### Quick Reference

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

### Helper Script

Use the helper script to ensure UV is always used for package installation:

```bash
# Install a package with UV
python scripts/install_package.py package_name

# Install multiple packages
python scripts/install_package.py package1 package2

# Install development dependencies
python scripts/install_package.py -e --dev
```

### Common Issues

If you encounter missing dependencies when running tests with Hatch:

1. Add the dependency to `pyproject.toml` under the appropriate section
1. Run `uv pip install -e ".[dev,test]"` to update your environment

## Testing and Coverage

### Quick Reference

```bash
# Run tests with coverage
hatch run test

# Run with verbose output
hatch run test -- -v

# Run specific tests
hatch run test -- -k "test_core"
```

### Coverage Configuration

The coverage configuration is defined in `pyproject.toml` with a minimum threshold of 60%.

### Improving Coverage

To improve the current coverage:

1. Focus on writing tests for modules with low coverage
1. Add tests for missing code paths in partially covered modules
1. Consider excluding difficult-to-test code paths with `# pragma: no cover`

## Version Management

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/) principles:

- MAJOR version for incompatible API changes
- MINOR version for backward-compatible functionality additions
- PATCH version for backward-compatible bug fixes

### Conventional Commits

We use [Conventional Commits](https://www.conventionalcommits.org/) to determine version bumps:

- `feat:` - Adds a new feature (MINOR version bump)
- `fix:` - Fixes a bug (PATCH version bump)
- `BREAKING CHANGE:` - Incompatible API change (MAJOR version bump)

### Manual Version Bumping

```bash
# Check what the next version would be
hatch run check-next-version

# Bump version (automatically determines level based on commits)
hatch run bump-version

# Prepare a release without pushing changes
hatch run prepare-release
```

### Release Process

1. Make changes and commit using conventional commit format
1. Merge to develop branch (CI/CD adds dev suffix)
1. Create PR from develop to master when ready for release
1. Merge PR to master and trigger release workflow manually

### Troubleshooting

If you encounter issues with version management:

1. Ensure you're using the conventional commit format
1. Check that your commits are on the correct branch
1. For manual fixes: `semantic-release version --new-version 1.2.3`
1. Debug version determination: `semantic-release version --print`

## Root User Support

When running on a Linux server, you may need to convert environments owned by different users. This requires running the converter as root.

### Automatic Ownership Preservation

When running as root, the converter will automatically preserve the original ownership of the source environment. This means that the new conda-forge environment will have the same owner and group as the original Anaconda environment, despite being created by the root user.

For example:

```bash
# Environment 'data_science' is owned by user 'analyst'
sudo conda-forge-converter -s data_science -t data_science_forge
# The new 'data_science_forge' environment will also be owned by 'analyst'
```

### Disabling Ownership Preservation

If you want to create environments owned by root even when running as root, you can use the `--no-preserve-ownership` flag:

```bash
sudo conda-forge-converter -s data_science -t data_science_forge --no-preserve-ownership
# The new 'data_science_forge' environment will be owned by root
```

### Security Considerations

When running as root:

- Be aware that this gives the converter the ability to change file ownership
- Consider using a dedicated service account instead of root when possible
- Ensure proper filesystem permissions are configured
