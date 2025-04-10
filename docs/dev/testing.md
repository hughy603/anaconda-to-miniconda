# Testing Guide

This document describes the testing approach, tools, and best practices for Conda-Forge Converter.

## Testing Philosophy

Testing is a critical part of maintaining the reliability and quality of Conda-Forge Converter. Our testing approach is based on:

1. **Comprehensive Coverage**: Aim for at least 80% code coverage
1. **Automated Testing**: Tests should run automatically in CI
1. **Test Isolation**: Tests should be independent and not affect each other
1. **Realistic Scenarios**: Tests should reflect real-world usage patterns

## Testing Tools

We use the following tools for testing:

- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking
- **GitHub Actions**: CI/CD

## Test Structure

Tests are organized in the `tests/` directory with the following structure:

```
tests/
├── unit/                  # Unit tests
│   ├── test_core.py
│   ├── test_cli.py
│   └── ...
├── integration/           # Integration tests
│   ├── test_conversion.py
│   ├── test_health.py
│   └── ...
├── functional/            # Functional/end-to-end tests
│   ├── test_basic_conversion.py
│   └── ...
├── conftest.py            # Shared fixtures
└── data/                  # Test data
    ├── environments/
    └── packages/
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run a specific test module
pytest tests/unit/test_core.py

# Run a specific test
pytest tests/unit/test_core.py::test_environment_discovery

# Run tests with verbose output
pytest -v
```

### Using hatch

```bash
# Run all tests
hatch run test

# Run with coverage
hatch run test:cov

# Run specific tests
hatch run test -- tests/unit/test_core.py
```

### Using tox

```bash
# Run tests in all supported Python versions
tox

# Run tests in a specific environment
tox -e py311
```

## Writing Tests

### Unit Tests

Unit tests should:

- Test a single function or method
- Use mocks for external dependencies
- Be fast to execute

Example unit test:

```python
def test_extract_packages():
    # Test setup
    env_data = {"name": "test_env", "dependencies": ["numpy=1.22.4", "pandas=1.4.2"]}

    # Call function
    result = extract_packages(env_data)

    # Assert expectations
    assert "numpy" in result
    assert result["numpy"] == "1.22.4"
    assert "pandas" in result
    assert result["pandas"] == "1.4.2"
```

### Integration Tests

Integration tests should:

- Test multiple components together
- Use actual files and data
- Verify component interaction

Example integration test:

```python
def test_environment_conversion():
    # Create test environment config
    config = {
        "source_env": "test_source",
        "target_env": "test_target",
        "python": "3.9",
        "dry_run": True,
    }

    # Mock environment detection
    with patch("conda_forge_converter.core.discover_environments") as discover_mock:
        discover_mock.return_value = {"test_source": "/path/to/env"}

        # Mock package extraction
        with patch("conda_forge_converter.core.extract_packages") as extract_mock:
            extract_mock.return_value = {"numpy": "1.22.4", "pandas": "1.4.2"}

            # Run conversion
            converter = EnvironmentConverter()
            result = converter.convert_environment(**config)

            # Verify interactions
            assert discover_mock.called
            assert extract_mock.called
            assert result["packages"] == {"numpy": "1.22.4", "pandas": "1.4.2"}
```

### Functional Tests

Functional tests should:

- Test end-to-end workflows
- Use real conda commands (when possible)
- Verify actual environment creation

Example functional test:

```python
@pytest.mark.functional
def test_basic_conversion(temp_conda_env):
    # Create a temporary test environment
    env_name = temp_conda_env(packages=["numpy=1.22.4", "pandas=1.4.2"])
    target_name = f"{env_name}_forge"

    # Run the CLI command
    result = subprocess.run(
        ["conda-forge-converter", "-s", env_name, "-t", target_name, "--dry-run"],
        capture_output=True,
        text=True,
    )

    # Verify output
    assert result.returncode == 0
    assert "numpy=1.22.4" in result.stdout
    assert "pandas=1.4.2" in result.stdout
```

## Test Fixtures

We use pytest fixtures to set up and tear down test resources:

```python
@pytest.fixture
def temp_conda_env():
    """Create a temporary conda environment for testing."""
    created_envs = []

    def _create_env(name=None, packages=None):
        if name is None:
            name = f"test_env_{uuid.uuid4().hex[:8]}"
        if packages is None:
            packages = []

        # Create environment
        cmd = ["conda", "create", "-n", name, "-y", "python=3.9"]
        cmd.extend(packages)
        subprocess.run(cmd, check=True)

        created_envs.append(name)
        return name

    yield _create_env

    # Clean up environments
    for env in created_envs:
        subprocess.run(["conda", "env", "remove", "-n", env, "-y"])
```

## Mocking

For testing components that interact with conda or the file system, we use mocking:

```python
@patch("conda_forge_converter.utils.run_command")
def test_discover_environments(mock_run):
    # Set up mock
    mock_run.return_value = (0, "base  *  /path/to/base\nenv1     /path/to/env1", "")

    # Call function
    envs = discover_environments()

    # Verify
    assert "base" in envs
    assert "env1" in envs
    assert envs["base"] == "/path/to/base"
    assert envs["env1"] == "/path/to/env1"
```

## Parameterized Tests

For testing multiple scenarios with similar logic:

```python
@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("package=1.0.0", ("package", "1.0.0")),
        ("package==1.0.0", ("package", "1.0.0")),
        ("package>=1.0.0", ("package", None)),
        ("package", ("package", None)),
    ],
)
def test_parse_package_spec(input_str, expected):
    assert parse_package_spec(input_str) == expected
```

## Testing CLI

For testing command-line interface:

```python
def test_cli_args():
    parser = create_argument_parser()
    args = parser.parse_args(["-s", "source_env", "-t", "target_env"])

    assert args.source_env == "source_env"
    assert args.target_env == "target_env"
    assert not args.dry_run
```

## Code Coverage

We track code coverage to ensure comprehensive testing:

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# Open the report
open htmlcov/index.html
```

## Continuous Integration

Tests run automatically on GitHub Actions:

- On every pull request
- When pushing to main branch
- On scheduled intervals

The CI workflow runs:

1. Tests on all supported Python versions
1. Code coverage reporting
1. Linting checks

### Local Testing of GitHub Actions Workflows

Before pushing changes to GitHub Actions workflows, you can test them locally using the tools provided in the `.github/local-testing` directory:

#### Prerequisites

1. Install Docker: <https://docs.docker.com/get-docker/>
1. Install act: <https://github.com/nektos/act#installation>
1. Install actionlint: <https://github.com/rhysd/actionlint#installation>

#### Validating Workflow Syntax

```bash
# Using pre-commit
pre-commit run actionlint --files .github/workflows/ci.yml

# Or directly with actionlint
actionlint .github/workflows/ci.yml
```

#### Testing Workflow Execution Locally

```bash
# Test with default push event
.github/local-testing/test-workflow.sh .github/workflows/ci.yml

# Test with pull_request event
.github/local-testing/test-workflow.sh .github/workflows/ci.yml pull_request
```

#### Testing with Python Matrix

```bash
# Test with Python 3.11
.github/local-testing/test-workflow.sh .github/workflows/ci.yml push python-version=3.11

# Test with Python 3.12
.github/local-testing/test-workflow.sh .github/workflows/ci.yml push python-version=3.12

# Test with both Python 3.11 and 3.12
.github/local-testing/test-python-versions.sh .github/workflows/ci.yml
```

#### VSCode Integration

The repository includes VSCode tasks for GitHub Actions testing:

1. Open the Command Palette (Ctrl+Shift+P)
1. Type "Tasks: Run Task"
1. Select one of the GitHub Actions testing tasks:
   - Validate Workflow
   - Test Workflow
   - Test with Python 3.11
   - Test with Python 3.12
   - Test Both Python Versions

For Windows users, refer to the `.github/local-testing/windows-setup-guide.md` for detailed setup instructions.

## Test Data

Test data is stored in `tests/data/` and includes:

- Sample environment files
- Package lists
- Mock command outputs

## Guidelines

1. Write tests before or alongside code (TDD/BDD)
1. Always add tests for bug fixes
1. When fixing a bug, first write a test that reproduces it
1. Test both success and failure paths
1. Use descriptive test names that explain what is being tested
1. Keep tests fast when possible
1. Separate slow tests with markers
