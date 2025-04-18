# GitHub Actions Workflow Validation

This guide explains how to validate GitHub Actions workflows locally before pushing changes to the repository.

## Overview

Our validation system provides two key capabilities:

1. **Syntax Validation**: Checking for syntax errors and best practices
1. **Execution Validation**: Running workflows in local containers

## Quick Start

```bash
# Validate all workflows
python validate-all-workflows.py
./validate-all-workflows.sh  # Unix/Linux wrapper

# Validate only changed workflows
python validate-all-workflows.py --changed-only
./validate-all-workflows.sh --changed-only

# Fast validation (dry run mode)
python validate-all-workflows.py --dry-run
./validate-all-workflows.sh --dry-run
```

## Prerequisites

- Python 3.11 or higher

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

- [pre-commit](https://pre-commit.com/) installed

- [act](https://github.com/nektos/act) installed

## Validation Methods

### 1. Command Line Validation

The `validate-all-workflows.py` script provides comprehensive validation:

```bash
# Basic usage
python validate-all-workflows.py
./validate-all-workflows.sh  # Unix/Linux wrapper

# Advanced options
python validate-all-workflows.py --changed-only --parallel --max-parallel 3 --secrets-file .github/local-secrets.json
./validate-all-workflows.sh --changed-only --parallel --max-parallel 3 --secrets-file .github/local-secrets.json
```

#### Available Options

| Option                | Description                                                |
| --------------------- | ---------------------------------------------------------- |
| `--changed-only`      | Only validate workflows that have changed                  |
| `--parallel`          | Run validations in parallel                                |
| `--max-parallel N`    | Maximum number of parallel jobs (default: 3)               |
| `--secrets-file FILE` | Path to secrets file (default: .github/local-secrets.json) |
| `--cache-path PATH`   | Path to cache directory (default: ./.act-cache)            |
| `--custom-image IMG`  | Use custom Docker image                                    |
| `--verbose`           | Enable verbose output                                      |
| `--dry-run`           | List workflows without running them                        |

### 2. VSCode Integration

VSCode tasks provide a convenient way to validate workflows:

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
1. Type "Tasks: Run Task"
1. Select one of the validation tasks:
   - "Validate Workflow Syntax"
   - "Validate All Workflows (Local Execution)"
   - "Validate Changed Workflows Only"
   - "Validate Workflows in Parallel"
   - "Validate Current Workflow (Local Execution)"
   - "Validate Workflows with Custom Settings"

### 3. Pre-commit Integration

Our pre-commit configuration includes hooks for workflow validation:

```bash
# Syntax validation (runs automatically on commit)
pre-commit run actionlint --all-files

# Fast validation of changed workflows (runs automatically on commit)
pre-commit run validate-changed-workflows

# Thorough validation (manual)
pre-commit run validate-workflows-execution --hook-stage manual

# Pre-push validation (runs automatically on push)
# (Requires pre-commit install --hook-type pre-push)
```

### 4. Continuous Integration

A dedicated workflow (`.github/workflows/validate-workflows.yml`) automatically validates workflows on pull requests that modify workflow files.

## Advanced Features

### Mock Secrets for Local Testing

Create a local secrets file by copying the template:

```bash
cp .github/local-secrets.json.template .github/local-secrets.json
# Edit .github/local-secrets.json with your test values
```

### Custom Docker Images

For more accurate local testing, use custom Docker images:

```bash
# Use the configuration directly
act -W .github/workflows/ci.yml $(cat act-custom-images.config)

# Or use with the validation scripts
./validate-all-workflows.sh --custom-image "ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"
```

### Testing Specific Jobs or Events

For faster validation of large workflows:

```bash
# Test only the 'build' job
python validate-all-workflows.py --workflow-file .github/workflows/ci.yml --job build
./github-actions-local.sh -w .github/workflows/ci.yml -j build

# Test a pull request event
python validate-all-workflows.py --workflow-file .github/workflows/ci.yml --default-event pull_request
./github-actions-local.sh -w .github/workflows/ci.yml -e pull_request
```

## Python Implementation

We've replaced the PowerShell implementation with a more robust Python implementation that provides better error handling and follows industry best practices. The Python implementation is structured as a package that can be easily extended or extracted into its own repository.

### Key Features

- **Improved Error Handling**: Detailed error messages with suggestions for fixes
- **Better YAML Parsing**: Proper parsing of GitHub Actions workflow files
- **Modular Design**: Clear separation of concerns for easier maintenance
- **Comprehensive Documentation**: Detailed documentation and examples
- **Cross-Platform**: Works on Windows, macOS, and Linux

### Usage

```bash
# Basic usage
python validate-all-workflows.py

# Validate only changed workflows
python validate-all-workflows.py --changed-only

# Validate a specific workflow
python validate-all-workflows.py --workflow-file .github/workflows/ci.yml

# Run validations in parallel
python validate-all-workflows.py --parallel --max-parallel 4

# Get help
python validate-all-workflows.py --help
```

### Python API

You can also use the Python API directly in your scripts:

```python
from github_actions_validator.config import Config
from github_actions_validator.discovery import find_workflows
from github_actions_validator.error_handling import ErrorReporter
from github_actions_validator.validators.execution import validate_workflows

# Create configuration
config = Config(changed_only=True, parallel=True, max_parallel=3)

# Find workflows
workflow_files = find_workflows(changed_only=config.changed_only)

# Create error reporter
error_reporter = ErrorReporter()

# Validate workflows
success, errors = validate_workflows(workflow_files, config, error_reporter)
```

## Troubleshooting

### Common Issues

1. **Docker not running**

   - Ensure Docker Desktop is running before validating workflows

1. **Missing dependencies**

   - Verify that act, pre-commit, and actionlint are installed

1. **Workflow runs locally but fails on GitHub**

   - Check for environment differences
   - Verify that secrets are properly configured

1. **Act cannot find workflow file**

   - Ensure paths use the correct format for your OS

1. **Custom Docker images not working**

   - Verify the image exists and is accessible

## Environment Variables

The following environment variables are automatically set during local testing:

| Variable                  | Value  | Purpose                                     |
| ------------------------- | ------ | ------------------------------------------- |
| `ACT`                     | `true` | Identify when running in act                |
| `ACT_LOCAL_TESTING`       | `true` | Identify when running in local testing mode |
| `SKIP_LONG_RUNNING_TESTS` | `true` | Skip long-running tests in local testing    |
