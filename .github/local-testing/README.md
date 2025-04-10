# GitHub Actions Local Testing

This directory contains tools for testing GitHub Actions workflows locally before committing changes.

## Overview

The local testing tools allow you to:

- Test GitHub Actions workflows locally without pushing to GitHub
- Test with specific matrix configurations (e.g., Python versions)
- Test with different event types (push, pull_request, etc.)
- Validate workflows before committing changes

## Prerequisites

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) - Required to run the workflow containers
1. [act](https://github.com/nektos/act#installation) - Tool for running GitHub Actions locally
1. PowerShell - Used by the scripts to run act

## Installation

### Installing act

#### Windows

```powershell
# Using Chocolatey
choco install act-cli

# Using Scoop
scoop install act
```

#### macOS

```bash
# Using Homebrew
brew install act
```

#### Linux

```bash
# Using the install script
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

## Usage

### Using PowerShell (Recommended)

#### Test a workflow

```powershell
# Test with default push event
.\github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml

# Test with pull_request event
.\github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request

# Test with specific Python version
.\github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -MatrixOverride "python-version=3.11"

# Test with specific job
.\github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -JobFilter "test"

# Test without Docker (dry run mode)
.\github\local-testing\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -DryRun
```

#### Test with multiple Python versions

```powershell
# Test with Python 3.11 and 3.12
.\github\local-testing\test-python-versions.ps1 -WorkflowFile .github/workflows/ci.yml
```

### Using Bash

#### Test a workflow

```bash
# Test with default push event
bash .github/local-testing/test-workflow.sh .github/workflows/ci.yml

# Test with pull_request event
bash .github/local-testing/test-workflow.sh .github/workflows/ci.yml pull_request

# Test with specific Python version
bash .github/local-testing/test-workflow.sh .github/workflows/ci.yml push python-version=3.11
```

#### Test with multiple Python versions

```bash
# Test with Python 3.11 and 3.12
bash .github/local-testing/test-python-versions.sh .github/workflows/ci.yml
```

## How It Works

The scripts:

1. Create a temporary directory in your home folder
1. Copy the repository files to the temporary directory
1. Initialize a git repository in the temporary directory
1. Create event and matrix configuration files as needed
1. Run act with the appropriate parameters
1. Clean up the temporary directory when done

This approach avoids issues with UNC paths and ensures a clean environment for each test run.

## Advanced Usage

### Using the act-runner.ps1 Script Directly

For more control, you can use the `act-runner.ps1` script directly:

```powershell
# Basic usage
.\github\local-testing\act-runner.ps1 -WorkflowFile .github/workflows/ci.yml -EventFile .github/local-testing/events/push.json

# With matrix override
.\github\local-testing\act-runner.ps1 -WorkflowFile .github/workflows/ci.yml -EventFile .github/local-testing/events/push.json -MatrixFile .github/local-testing/matrix-input.json

# Keep the temporary directory for debugging
.\github\local-testing\act-runner.ps1 -WorkflowFile .github/workflows/ci.yml -EventFile .github/local-testing/events/push.json -KeepTemp

# Specify a different platform and Docker image
.\github\local-testing\act-runner.ps1 -WorkflowFile .github/workflows/ci.yml -EventFile .github/local-testing/events/push.json -Platform ubuntu-22.04 -DockerImage ghcr.io/catthehacker/ubuntu:act-22.04

# Run without Docker (dry run mode)
.\github\local-testing\act-runner.ps1 -WorkflowFile .github/workflows/ci.yml -EventFile .github/local-testing/events/push.json -DryRun
```

## Troubleshooting

### Docker Issues

- Ensure Docker Desktop is running
- Make sure you have enough disk space for the Docker images
- If you see permission errors, try running Docker Desktop as administrator

### Path Issues

- The scripts handle path conversion automatically
- If you see path-related errors, try using the PowerShell scripts instead of bash

### Git Issues

- The scripts initialize a git repository in the temporary directory
- If you see git-related errors, make sure git is installed and in your PATH
