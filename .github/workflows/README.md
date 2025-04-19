# GitHub Actions Local Testing

This directory contains scripts and configuration for testing GitHub Actions workflows locally.

## Overview

We provide two scripts for local testing:

1. `local-test.sh` - For Unix/Linux/macOS users
1. `local-test.ps1` - For Windows users

Both scripts provide the same functionality and use [nektos/act](https://github.com/nektos/act) under the hood.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [act](https://github.com/nektos/act) installed:
  - macOS/Linux: `brew install act`
  - Windows: `choco install act-cli` or `scoop install act`

## Quick Start

### Unix/Linux/macOS

```bash
# Make the script executable
chmod +x .github/workflows/local-test.sh

# Run a workflow
.github/workflows/local-test.sh -w .github/workflows/ci.yml
```

### Windows

```powershell
# Run a workflow
.\github\workflows\local-test.ps1 -WorkflowFile .github\workflows\ci.yml
```

## Features

- Cross-platform support (Unix/Linux/macOS/Windows)
- Automatic event file creation
- Support for different event types (push, pull_request, etc.)
- Job filtering
- Platform selection
- Workspace binding
- Verbose output
- Action caching
- Colorized output
- Error handling and validation

## Usage

### Basic Usage

**Unix/Linux/macOS:**

```bash
.github/workflows/local-test.sh -w .github/workflows/ci.yml
```

**Windows:**

```powershell
.\github\workflows\local-test.ps1 -WorkflowFile .github\workflows\ci.yml
```

### Advanced Options

**Unix/Linux/macOS:**

```bash
# Test a specific job
.github/workflows/local-test.sh -w .github/workflows/ci.yml -j build

# Test with a different event type
.github/workflows/local-test.sh -w .github/workflows/ci.yml -e pull_request

# Enable verbose output
.github/workflows/local-test.sh -w .github/workflows/ci.yml -v

# Bind workspace to container
.github/workflows/local-test.sh -w .github/workflows/ci.yml -b
```

**Windows:**

```powershell
# Test a specific job
.\github\workflows\local-test.ps1 -WorkflowFile .github\workflows\ci.yml -JobFilter build

# Test with a different event type
.\github\workflows\local-test.ps1 -WorkflowFile .github\workflows\ci.yml -EventType pull_request

# Enable verbose output
.\github\workflows\local-test.ps1 -WorkflowFile .github\workflows\ci.yml -Verbose

# Bind workspace to container
.\github\workflows\local-test.ps1 -WorkflowFile .github\workflows\ci.yml -BindWorkspace
```

## Event Templates

The scripts use template files to create event context for different trigger types. These templates are stored in `.github/events/templates/`:

- `push.json` - Template for push events
- `pull_request.json` - Template for pull request events

When you run the scripts with a specific event type, they will:

1. Check if an event file already exists at `.github/events/<event_type>.json`
1. If not, copy the template from `.github/events/templates/<event_type>.json`
1. If no template exists, create a basic event file

You can customize these templates or create new ones for other event types (e.g., `issue_comment.json`, `release.json`).

## Best Practices

1. **Use Environment Variables for Conditional Execution**

   Add conditional logic to your workflows to handle local testing:

   ```yaml
   # Skip steps that won't work locally
   - name: Upload to S3
     if: ${{ env.ACT != 'true' }}
     uses: aws-actions/aws-s3-upload@v1
   ```

1. **Mock External Services**

   For actions that interact with external services, consider adding mock implementations:

   ```yaml
   - name: Deploy to Production
     if: ${{ env.ACT != 'true' }}
     uses: some-deploy-action@v1

   - name: Mock Deployment (Local Testing)
     if: ${{ env.ACT == 'true' }}
     run: echo "Mocking deployment process for local testing"
   ```

1. **Handle Docker-in-Docker Scenarios**

   For workflows that use Docker-related actions:

   ```yaml
   - name: Build and Push Docker Image
     if: ${{ env.ACT != 'true' }}
     uses: docker/build-push-action@v5

   - name: Local Docker Build
     if: ${{ env.ACT == 'true' }}
     run: |
       docker build -t myapp:local .
       echo "Docker image built locally"
   ```

## Troubleshooting

### Common Issues

1. **"Unknown action" error**

   - Some third-party actions may not be compatible with act
   - Use conditional logic to skip these actions during local testing

1. **Docker-related issues**

   - Ensure Docker Desktop is running
   - For Docker-in-Docker scenarios, use the `--bind` option

1. **Authentication issues**

   - The script sets a dummy `GITHUB_TOKEN` for local testing
   - For actions requiring specific tokens, add them to your local environment

1. **Platform compatibility**

   - act runs everything in Linux containers, even when simulating Windows or macOS
   - Platform-specific commands may not work as expected

1. **Path handling issues on Windows**

   - The script automatically converts Windows backslashes to forward slashes
   - You can use either format in your command parameters

## Contributing

Feel free to submit issues and enhancement requests!
