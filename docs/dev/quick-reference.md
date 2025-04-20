# Developer Quick Reference

This guide provides quick reference information for common development tasks, commands, and troubleshooting tips for the Conda-Forge Converter project.

## Common Commands

### Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Install tools
pipx install uv
pipx install pre-commit

# Set up development environment
uv pip install -e ".[dev,test]"
pre-commit install
```

### Git Workflow

```bash
# Update local copy
git checkout develop
git pull

# Create feature branch
git checkout -b feature/your-feature-name

# Check status
git status

# Add files
git add .

# Commit changes (use conventional format)
git commit -m "feat(component): add new feature"

# Push changes
git push origin feature/your-feature-name
```

### Testing

```bash
# Run all tests
hatch run test:run

# Run with coverage
hatch run test

# Run specific test file
hatch run test:run tests/test_specific.py

# Run specific test
hatch run test:run tests/test_specific.py::test_function
```

### Code Quality

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Format code
ruff format .

# Run linting
ruff check .

# Run type checking
pyright
```

### Dependency Management

```bash
# Lock dependencies
uv run deps-lock

# Update dependencies
uv run deps-update

# Add a new dependency
# 1. Edit pyproject.toml
# 2. Run: uv run deps-lock
```

### Documentation

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### GitHub Actions Local Testing

```bash
# Validate workflow syntax
actionlint .github/workflows/ci.yml

# Test workflow with push event
.github/local-testing/test-workflow.sh .github/workflows/ci.yml

# Test workflow with pull_request event
.github/local-testing/test-workflow.sh .github/workflows/ci.yml pull_request

# Test with Python 3.11
.github/local-testing/test-workflow.sh .github/workflows/ci.yml push python-version=3.11

# Test with Python 3.12
.github/local-testing/test-workflow.sh .github/workflows/ci.yml push python-version=3.12

# Test with both Python versions
.github/local-testing/test-python-versions.sh .github/workflows/ci.yml
```

## Conventional Commits Cheat Sheet

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
| ---------- | ----------------------------------------------------- |
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Changes that don't affect code meaning |
| `refactor` | Code change that neither fixes a bug nor adds feature |
| `perf` | Performance improvement |
| `test` | Adding or correcting tests |
| `build` | Changes to build system or dependencies |
| `ci` | Changes to CI configuration |
| `chore` | Other changes that don't modify src or test files |

### Common Scopes

- `cli`: Command-line interface
- `core`: Core functionality
- `utils`: Utility functions
- `deps`: Dependencies
- `tests`: Test suite
- `docs`: Documentation

### Examples

```
feat(cli): add verbose output option
fix(core): resolve package resolution error
docs: update installation instructions
refactor(utils): improve error handling
test(cli): add tests for new verbose option
```

## PR Process Checklist

### Before Creating PR

- [ ] All tests pass locally
- [ ] Pre-commit checks pass
- [ ] Documentation is updated
- [ ] Code follows project style guidelines
- [ ] Commits follow conventional commit format

### PR Template Sections

- Description
- Related Issues
- Type of Change
- Implementation Details
- Testing Performed
- Documentation
- Checklist

### After PR is Created

- Address CI failures
- Respond to review comments
- Keep PR updated with target branch

## Troubleshooting

### Pre-commit Issues

**Issue**: Hooks failing

**Solution**:

```bash
# Update hooks
pre-commit autoupdate

# Clean cache
pre-commit clean

# Run again
pre-commit run --all-files
```

### Dependency Issues

**Issue**: Dependency resolution conflicts

**Solution**:

```bash
# Clear cache and try again
uv cache clean
uv pip install -e ".[dev,test]"
```

### Git Issues

**Issue**: Merge conflicts

**Solution**:

```bash
# Update target branch
git checkout develop
git pull

# Rebase feature branch
git checkout feature/your-feature-name
git rebase develop

# Resolve conflicts and continue
git add .
git rebase --continue

# Force push (with care!)
git push --force-with-lease origin feature/your-feature-name
```

**Issue**: Accidentally committed to wrong branch

**Solution**:

```bash
# Stash changes
git stash

# Switch to correct branch
git checkout correct-branch

# Apply stashed changes
git stash pop
```

### Test Issues

**Issue**: Tests failing locally but passing in CI

**Solution**:

```bash
# Clean pytest cache
pytest --cache-clear

# Check for environment differences
uv pip install -e ".[dev,test]"
```

**Issue**: Slow tests

**Solution**:

```bash
# Run only specific tests
pytest tests/test_specific.py

# Use pytest-xdist for parallel testing
pytest -xvs
```

## Common File Locations

- **Source code**: `src/conda_forge_converter/`
- **Tests**: `tests/`
- **Documentation**: `docs/`
- **Build configuration**: `pyproject.toml`
- **CI configuration**: `.github/workflows/`
- **Pre-commit configuration**: `.pre-commit-config.yaml`

## Environment Variables

| Variable | Purpose | Example |
| --------------------------------- | --------------------------------- | -------------------------- |
| `CONDA_FORGE_CONVERTER_LOG_LEVEL` | Set logging level | `DEBUG`, `INFO`, `WARNING` |
| `CONDA_FORGE_CONVERTER_CACHE_DIR` | Override cache directory location | `/path/to/cache` |
| `CONDA_FORGE_CONVERTER_NO_CACHE` | Disable caching | `1`, `true`, `yes` |

## Release Process Quick Reference

1. **Create Release Branch**:

   ```bash
   git checkout develop
   git pull
   git checkout -b release/vX.Y.Z
   ```

1. **Bump Version**:

   ```bash
   cz bump
   ```

1. **Create PR to Main**

1. **After Merge, Tag Release**:

   ```bash
   git checkout main
   git pull
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

## Tool Configuration Quick Reference

### pyproject.toml Sections

- `[build-system]`: Hatch configuration
- `[project]`: Package metadata and dependencies
- `[project.optional-dependencies]`: Dev and test dependencies
- `[tool.hatch.version]`: Version management
- `[tool.hatch.envs.test]`: Test environment and scripts
- `[tool.ruff]`: Ruff linter configuration
- `[tool.pyright]`: Type checking configuration
- `[tool.pytest.ini_options]`: Pytest configuration
- `[tool.commitizen]`: Commitizen configuration

### pre-commit Hooks

- Code formatting: Ruff
- Linting: Ruff, pre-commit-hooks
- Type checking: Pyright
- Commit message: Commitizen
- Dependency locking: UV
- Security: Gitleaks

## Additional Resources

- [Full Developer Workflow Guide](workflow.md)
- [Conventional Commits Guide](conventional-commits.md)
- [Build Tools Guide](build-tools.md)
- [PR Process Guide](pr-process.md)
