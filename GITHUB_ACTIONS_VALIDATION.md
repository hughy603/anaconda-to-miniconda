# GitHub Actions Workflow Validation

This guide explains how to validate GitHub Actions workflows locally before pushing changes to the repository.

## Overview

Our validation system provides two key capabilities:

1. **Syntax Validation**: Checking for syntax errors and best practices
1. **Execution Validation**: Running workflows in local containers

## Quick Start

```bash
# Validate all workflows
./validate-all-workflows.sh
.\validate-all-workflows.ps1

# Validate only changed workflows
./validate-all-workflows.sh --changed-only
.\validate-all-workflows.ps1 -ChangedOnly

# Fast validation (dry run mode)
./validate-all-workflows.sh --dry-run
.\validate-all-workflows.ps1 -DryRun
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [pre-commit](https://pre-commit.com/) installed
- [act](https://github.com/nektos/act) installed

## Validation Methods

### 1. Command Line Validation

The `validate-all-workflows.sh` (or `.ps1`) script provides comprehensive validation:

```bash
# Basic usage
./validate-all-workflows.sh
.\validate-all-workflows.ps1

# Advanced options
./validate-all-workflows.sh --changed-only --parallel --max-parallel 3 --secrets-file .github/local-secrets.json
.\validate-all-workflows.ps1 -ChangedOnly -Parallel -MaxParallel 3 -SecretsFile .github/local-secrets.json
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
./github-actions-local.sh -w .github/workflows/ci.yml -j build
.\github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -JobFilter build

# Test a pull request event
./github-actions-local.sh -w .github/workflows/ci.yml -e pull_request
.\github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request
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
