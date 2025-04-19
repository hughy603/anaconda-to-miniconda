# Local Testing of GitHub Actions Workflows

This document describes how to test GitHub Actions workflows locally using [act](https://github.com/nektos/act).

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop) installed and running
- [act](https://github.com/nektos/act#installation) installed
- PowerShell (for Windows users)

## Testing Workflows

### Using the PowerShell Script

The simplest way to test workflows is using the `test-workflows.ps1` script:

```powershell
# Test with default settings (push event)
.\test-workflows.ps1

# Test a specific workflow with pull_request event
.\test-workflows.ps1 -WorkflowFile ".github/workflows/validate-github-actions.yml" -EventType "pull_request"

# Test a specific job
.\test-workflows.ps1 -JobFilter "validate"
```

### Using act Directly

You can also use act directly with its built-in event generation:

```bash
# Test with push event
act -W .github/workflows/validate-github-actions.yml -e push

# Test with pull_request event
act -W .github/workflows/validate-github-actions.yml -e pull_request

# Test a specific job
act -W .github/workflows/validate-github-actions.yml -e push -j validate
```

## Environment Variables

The following environment variables are set by default:

- `ACT=true`: Indicates we're running in act
- `ACT_LOCAL_TESTING=true`: Indicates we're running in local testing mode
- `GITHUB_TOKEN=local-testing-token`: A dummy token for local testing

## Troubleshooting

1. **Docker not running**

   - Start Docker Desktop
   - Verify Docker is running with `docker info`

1. **act not installed**

   - Install act using the official installation method for your platform
   - Verify installation with `act --version`

1. **Workflow not found**

   - Make sure you're in the correct directory
   - Verify the workflow file path is correct

1. **Job not found**

   - Check the job name in your workflow file
   - Make sure the job is not skipped due to conditions
