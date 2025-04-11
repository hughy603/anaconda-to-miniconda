# GitHub Actions Local Testing

This directory contains scripts and configuration files for testing GitHub Actions workflows locally using [act](https://github.com/nektos/act).

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [act](https://github.com/nektos/act) installed

## Scripts

### test-workflow.ps1

This PowerShell script allows you to test GitHub Actions workflows locally.

```powershell
# Test the CI workflow
.\.github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml

# Test with a specific event type
.\.github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request

# Test with a matrix override
.\.github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -MatrixOverride "python-version=3.11"

# Test a specific job
.\.github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -JobFilter "test"

# Dry run (don't actually run Docker)
.\.github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -DryRun
```

### test-workflow.sh

This Bash script provides the same functionality as test-workflow.ps1 but for Unix-like systems.

```bash
# Test the CI workflow
./test-workflow.sh .github/workflows/ci.yml

# Test with a specific event type
./test-workflow.sh .github/workflows/ci.yml pull_request

# Test with a matrix override
./test-workflow.sh .github/workflows/ci.yml push python-version=3.11
```

### act-runner.ps1

This PowerShell script is used by test-workflow.ps1 to run GitHub Actions workflows locally. It handles:

- Creating a temporary directory
- Copying repository files
- Setting up a git repository
- Running act with the appropriate parameters

## Local Testing Workflow Files

For workflows that require specific environment setup, we provide local testing versions of the workflow files:

- `ci-local.yml`: A modified version of ci.yml that works better with local testing

These local testing workflow files are automatically used when running the test-workflow.ps1 script with the corresponding workflow file.

## Troubleshooting

### Docker Issues

If you encounter Docker-related issues:

1. Make sure Docker Desktop is running
1. Try running with the `-DryRun` flag to see the commands that would be executed
1. Check Docker Desktop settings to ensure it has enough resources

### Act Issues

If you encounter issues with act:

1. Make sure act is installed and in your PATH
1. Try running act directly to see if there are any configuration issues
1. Check the [act documentation](https://github.com/nektos/act) for more information

### Workflow Issues

If the workflow runs but fails:

1. Check the error messages in the output
1. Look for missing dependencies or configuration
1. Try running with a matrix override to test a specific configuration
