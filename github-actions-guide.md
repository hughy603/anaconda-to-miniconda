# GitHub Actions Guide

This comprehensive guide covers everything you need to know about GitHub Actions in this project, including local testing, workflow configuration, and best practices.

## Table of Contents

1. [Introduction](#introduction)
1. [Local Testing](#local-testing)
1. [Modular Actions](#modular-actions)
1. [Workflow Configuration](#workflow-configuration)
1. [Progressive Testing](#progressive-testing)
1. [Python Testing](#python-testing)
1. [Best Practices](#best-practices)
1. [Troubleshooting](#troubleshooting)
1. [Decision Tree](#decision-tree)
1. [Quick Reference](#quick-reference)

## Introduction

GitHub Actions automate our CI/CD pipeline, ensuring code quality and reliability. This guide explains how to work with our GitHub Actions workflows, including how to test them locally before pushing changes.

## Local Testing

### Setup Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [act](https://github.com/nektos/act) installed
- [actionlint](https://github.com/rhysd/actionlint) installed (optional, for static analysis)

### Key Concepts

1. **Direct Testing**: Test original workflow files directly instead of maintaining copies
1. **Runtime Configuration**: Use environment variables and conditionals to adapt workflows for local testing
1. **Simplified Scripts**: Use minimal wrapper scripts focused on common testing scenarios

### Common Commands

#### Basic Workflow Testing

```bash
# Test a workflow with default settings (push event)
.github/local-testing/local-test.sh .github/workflows/ci.yml

# Test with a specific event type
.github/local-testing/local-test.sh .github/workflows/ci.yml pull_request

# Test a specific job
.github/local-testing/local-test.sh .github/workflows/ci.yml push test

# Test with a matrix override
.github/local-testing/local-test.sh .github/workflows/ci.yml push "" python-version=3.11
```

#### Testing with Different Python Versions

```bash
# Test with Python 3.11
.github/local-testing/local-test.sh .github/workflows/ci.yml push "" python-version=3.11

# Test with Python 3.12
.github/local-testing/local-test.sh .github/workflows/ci.yml push "" python-version=3.12

# Test with both Python versions
.github/local-testing/test-python-versions.sh .github/workflows/ci.yml
```

#### Workflow Validation

```bash
# Validate a workflow file
.github/local-testing/validate-workflow.sh .github/workflows/ci.yml

# Or use actionlint directly
actionlint .github/workflows/ci.yml
```

### PowerShell Commands

For Windows users, we provide PowerShell scripts with similar functionality:

```powershell
# Test a workflow with default settings
.github/local-testing/local-test.ps1 .github/workflows/ci.yml

# Test with a specific event type
.github/local-testing/local-test.ps1 .github/workflows/ci.yml -EventType pull_request

# Test a specific job
.github/local-testing/local-test.ps1 .github/workflows/ci.yml -EventType push -JobFilter test

# Test with Python 3.11
.github/local-testing/local-test.ps1 .github/workflows/ci.yml -PythonVersion 3.11

# Test with both Python versions
.github/local-testing/test-python-versions.ps1 .github/workflows/ci.yml
```

### VSCode Tasks

Press `Ctrl+Shift+P` and select "Tasks: Run Task", then choose one of:

- **Validate Workflow**: Run static analysis on a workflow file
- **Test Workflow**: Test a workflow with customizable parameters
- **Test with Python 3.11**: Test a workflow with Python 3.11
- **Test with Python 3.12**: Test a workflow with Python 3.12
- **Test Both Python Versions**: Test a workflow with both Python versions

## Modular Actions

This project uses modular composite actions to improve reusability and maintainability. These actions are stored in the `.github/actions/` directory.

### Available Actions

- **setup-python-env**: Sets up Python with UV and installs dependencies
- **diagnostic-info**: Collects and displays diagnostic information about the environment
- **run-tests**: Runs tests with configurable options and proper error handling
- **run-linting**: Runs linting and type checking with configurable options

### Using Composite Actions

To use these actions in your workflows:

```yaml
- name: Setup Python
  uses: ./.github/actions/setup-python-env
  with:
    python-version: "3.11"
    install-extras: "dev,test"

- name: Run tests
  uses: ./.github/actions/run-tests
  with:
    test-type: "unit"
    coverage: true
```

## Workflow Configuration

### Making Workflows Compatible with Local Testing

Add conditionals to your workflows to adapt them for local testing:

```yaml
# Example conditional for simplified testing
- name: Run tests
  run: |
    if [[ "${{ env.ACT_LOCAL_TESTING }}" == "true" ]]; then
      # Simplified version for local testing
      pytest -xvs tests/
    else
      # Full version for GitHub
      pytest --cov=src/ --cov-report=xml tests/
    fi

# Example conditional to skip steps in local testing
- name: Upload to codecov
  if: ${{ env.ACT_LOCAL_TESTING != 'true' }}
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml

# Example matrix simplification for local testing
strategy:
  matrix:
    python-version: ${{ env.ACT_LOCAL_TESTING == 'true' && fromJSON('["3.11"]') || fromJSON('["3.11", "3.12"]') }}
    os: ${{ env.ACT_LOCAL_TESTING == 'true' && fromJSON('["ubuntu-latest"]') || fromJSON('["ubuntu-latest", "windows-latest", "macos-latest"]') }}
```

### Environment Variables

The following environment variables are automatically set during local testing:

| Variable                  | Value  | Purpose                                     |
| ------------------------- | ------ | ------------------------------------------- |
| `ACT_LOCAL_TESTING`       | `true` | Identify when running in local testing mode |
| `SKIP_DOCKER_BUILDS`      | `true` | Skip Docker build steps in local testing    |
| `SKIP_LONG_RUNNING_TESTS` | `true` | Skip long-running tests in local testing    |

### Centralized Configuration

The `.github/workflow-config.yml` file centralizes configuration for all workflows. This makes it easier to maintain consistent settings across multiple workflows.

```yaml
# Example workflow-config.yml
python:
  versions:
    - "3.11"
    - "3.12"
  default: "3.11"

testing:
  parallel: true
  coverage:
    enabled: true
    threshold: 80
```

## Progressive Testing

Our workflows use a progressive testing strategy to optimize CI/CD performance:

1. **Quick Tests**: Fast, critical tests run first
1. **Full Tests**: Comprehensive tests run only if quick tests pass
1. **Integration Tests**: More complex tests run only on specific branches or PRs

This approach saves time by failing fast on critical issues and only running more time-consuming tests when necessary.

```yaml
jobs:
  quick-tests:
    # Run fast tests first

  full-tests:
    needs: quick-tests
    if: success()
    # Run comprehensive tests

  integration-tests:
    needs: full-tests
    if: success() && (github.ref == 'refs/heads/main' || github.event_name == 'pull_request')
    # Run integration tests
```

## Python Testing

### Build Tools

This project uses the following build tools:

- **UV**: Fast Python package installer and resolver
- **Hatch**: Modern Python project management

We no longer use Poetry for dependency management.

### Testing with UV and Hatch

```bash
# Install dependencies with UV
uv pip install -e ".[dev,test]" --system

# Run tests with Hatch
hatch run test

# Run linting with Hatch
hatch run lint

# Run type checking with Hatch
hatch run type-check
```

### Workflow Configuration for Python Testing

Our CI workflow is configured to use UV for dependency installation and Hatch for running tests:

```yaml
- name: Install UV
  shell: bash
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "$HOME/.cargo/bin" >> "$GITHUB_PATH"

- name: Install dependencies
  run: |
    uv pip install -e ".[dev,test]" --system

- name: Run tests
  run: |
    hatch run test
```

## Best Practices

1. **Test Before Committing**: Always test workflow changes locally before committing
1. **Start Simple**: Begin with basic tests before adding complexity
1. **Use Static Analysis**: Combine runtime testing with static analysis using actionlint
1. **Test Specific Jobs**: Test the specific jobs you've modified rather than the entire workflow
1. **Keep Local Testing Fast**: Optimize workflows for quick local testing with conditionals
1. **Document Adaptations**: Document any adaptations made for local testing
1. **Maintain Compatibility**: Ensure workflows work both locally and on GitHub
1. **Use UV and Hatch**: Always use UV for dependency installation and Hatch for running tests
1. **Use Composite Actions**: Break down workflows into reusable components
1. **Implement Progressive Testing**: Run fast tests first, then more comprehensive tests

## Troubleshooting

### Common Issues and Solutions

#### Workflow Fails with "Resource not accessible by integration" Error

**Problem**: The workflow doesn't have permission to access resources.

**Solution**:

1. Check the `permissions` section in your workflow
1. Ensure the repository has the correct permissions settings
1. For organization repositories, check organization settings

#### Workflow Fails with "No space left on device" Error

**Problem**: The GitHub runner has run out of disk space.

**Solution**:

1. Clean up workspace before or during the job
1. Use `actions/cache` more selectively
1. Remove unnecessary artifacts

#### Local Testing with Act Fails with "Unknown action" Error

**Problem**: Act cannot find the action specified in the workflow.

**Solution**:

1. Ensure you're using the correct action syntax for local testing
1. For composite actions, use relative paths: `./.github/actions/my-action`
1. For third-party actions, check if they're compatible with Act

#### Tests Pass Locally but Fail in CI

**Problem**: Environment differences between local and CI.

**Solution**:

1. Use the diagnostic-info action to compare environments
1. Ensure dependencies are properly specified
1. Check for hardcoded paths or environment-specific code

### Docker Issues

- Ensure Docker Desktop is running
- Check Docker Desktop has sufficient resources allocated
- Try restarting Docker Desktop

### Act Issues

- Ensure act is installed and in your PATH
- Check for act configuration issues with `act --help`
- Verify your `.actrc` file is correctly configured

### Workflow Issues

- Use `--verbose` flag for more detailed output: `.github/local-testing/local-test.sh .github/workflows/ci.yml push "" "" --verbose`
- Check for missing secrets or environment variables
- Verify workflow file syntax with actionlint

### Debugging Workflows

To enable debug mode for a workflow:

1. **GitHub**: Set the `ACTIONS_RUNNER_DEBUG` secret to `true`
1. **Local**: Use the `--debug` flag with Act
1. **Workflow**: Use the debug input parameter if available

```yaml
# Trigger workflow with debug mode
on:
  workflow_dispatch:
    inputs:
      debug:
        description: 'Enable debug mode'
        required: false
        default: false
        type: boolean
```

## Decision Tree

Use this decision tree to diagnose and fix common workflow issues:

```
Workflow Failed
├── Syntax Error
│   ├── YAML Syntax Issue
│   │   └── Solution: Validate YAML with actionlint
│   └── Expression Syntax Issue
│       └── Solution: Check expression syntax in GitHub Actions docs
├── Action Error
│   ├── Action Not Found
│   │   └── Solution: Check action reference and version
│   └── Action Failed
│       └── Solution: Check action inputs and requirements
├── Test Failure
│   ├── Test Logic Error
│   │   └── Solution: Debug test with verbose output
│   └── Environment Issue
│       └── Solution: Use diagnostic-info action to check environment
└── Resource Error
    ├── Timeout
    │   └── Solution: Optimize workflow or increase timeout
    ├── Out of Disk Space
    │   └── Solution: Clean up workspace or reduce artifacts
    └── Memory Error
        └── Solution: Reduce parallel processes or optimize memory usage
```

## Quick Reference

### Testing CI Workflow

```bash
# Test the entire CI workflow
.github/local-testing/local-test.sh .github/workflows/ci.yml

# Test only the test job
.github/local-testing/local-test.sh .github/workflows/ci.yml push test

# Test with Python 3.11
.github/local-testing/local-test.sh .github/workflows/ci.yml push "" python-version=3.11
```

### Testing Release Workflow

```bash
# Test the release workflow with workflow_dispatch event
.github/local-testing/local-test.sh .github/workflows/release.yml workflow_dispatch

# Test only the build job
.github/local-testing/local-test.sh .github/workflows/release.yml workflow_dispatch build
```

### Testing Documentation Workflow

```bash
# Test the docs workflow
.github/local-testing/local-test.sh .github/workflows/docs.yml

# Test only the build job
.github/local-testing/local-test.sh .github/workflows/docs.yml push build
```

### Setting Up Workflows for a New Project

```bash
# PowerShell
.github/setup-workflows.ps1 -ProjectType python -PythonVersion 3.11 -UseUV -UseHatch

# Bash
.github/setup-workflows.sh --project-type python --python-version 3.11 --use-uv --use-hatch
```
