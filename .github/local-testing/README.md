# GitHub Actions Local Testing

This directory contains tools for testing GitHub Actions workflows locally without maintaining duplicate workflow files.

## Important Note

This documentation has been consolidated into the main GitHub Actions guide. Please refer to the [GitHub Actions Guide](../../github-actions-guide.md) for the most up-to-date information.

The scripts in this directory are still used for local testing, but the documentation has been moved to the main guide for better organization.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [act](https://github.com/nektos/act) installed
- [actionlint](https://github.com/rhysd/actionlint) installed (optional, for static analysis)

## Quick Start

### Bash/Linux/macOS

```bash
# Test a workflow with default settings (push event)
.github/local-testing/local-test.sh .github/workflows/ci.yml

# Test with a specific event type
.github/local-testing/local-test.sh .github/workflows/ci.yml pull_request

# Test a specific job
.github/local-testing/local-test.sh .github/workflows/ci.yml push test

# Test with a matrix override
.github/local-testing/local-test.sh .github/workflows/ci.yml push "" python-version=3.11

# Test with both Python versions
.github/local-testing/test-python-versions.sh .github/workflows/ci.yml

# Validate a workflow
.github/local-testing/validate-workflow.sh .github/workflows/ci.yml
```

### PowerShell/Windows

```powershell
# Test a workflow with default settings (push event)
.github/local-testing/local-test.ps1 -WorkflowFile .github/workflows/ci.yml

# Test with a specific event type
.github/local-testing/local-test.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request

# Test a specific job
.github/local-testing/local-test.ps1 -WorkflowFile .github/workflows/ci.yml -EventType push -JobFilter test

# Test with a matrix override
.github/local-testing/local-test.ps1 -WorkflowFile .github/workflows/ci.yml -EventType push -MatrixOverride python-version=3.11

# Test with both Python versions
.github/local-testing/test-python-versions.ps1 -WorkflowFile .github/workflows/ci.yml

# Validate a workflow
.github/local-testing/validate-workflow.ps1 -WorkflowFile .github/workflows/ci.yml
```

## VSCode Integration

This repository includes VSCode tasks for easy access to these tools. Press `Ctrl+Shift+P` and select "Tasks: Run Task", then choose one of:

- **Validate Workflow**: Run static analysis on a workflow file
- **Test Workflow**: Test a workflow with customizable parameters
- **Test with Python 3.11**: Test a workflow with Python 3.11
- **Test with Python 3.12**: Test a workflow with Python 3.12
- **Test Both Python Versions**: Test a workflow with both Python versions

## Scripts

### local-test.sh / local-test.ps1

This script allows you to test GitHub Actions workflows locally using act.

```bash
# Bash/Linux/macOS
.github/local-testing/local-test.sh <workflow-file> [event-type] [job-filter] [matrix-override] [additional-args]

# PowerShell/Windows
.github/local-testing/local-test.ps1 -WorkflowFile <workflow-file> [-EventType <event-type>] [-JobFilter <job-filter>] [-MatrixOverride <matrix-override>] [<additional-args>]
```

Parameters:

- `workflow-file`: Path to the workflow file to test (required)
- `event-type`: Event type to simulate (default: push)
- `job-filter`: Specific job to run (default: all jobs)
- `matrix-override`: Matrix override in the format key=value (default: none)
- `additional-args`: Additional arguments to pass to act

### test-python-versions.sh / test-python-versions.ps1

This script tests a workflow with both Python 3.11 and 3.12.

```bash
# Bash/Linux/macOS
.github/local-testing/test-python-versions.sh <workflow-file> [event-type] [job-filter] [additional-args]

# PowerShell/Windows
.github/local-testing/test-python-versions.ps1 -WorkflowFile <workflow-file> [-EventType <event-type>] [-JobFilter <job-filter>] [<additional-args>]
```

Parameters:

- `workflow-file`: Path to the workflow file to test (required)
- `event-type`: Event type to simulate (default: push)
- `job-filter`: Specific job to run (default: all jobs)
- `additional-args`: Additional arguments to pass to act

### validate-workflow.sh / validate-workflow.ps1

This script validates a workflow file using actionlint and custom checks.

```bash
# Bash/Linux/macOS
.github/local-testing/validate-workflow.sh <workflow-file>

# PowerShell/Windows
.github/local-testing/validate-workflow.ps1 -WorkflowFile <workflow-file>
```

Parameters:

- `workflow-file`: Path to the workflow file to validate (required)

## Making Workflows Compatible with Local Testing

To make workflows compatible with local testing, add conditionals based on the `ACT_LOCAL_TESTING` environment variable:

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

## Environment Variables

The following environment variables are automatically set during local testing:

| Variable                  | Value  | Purpose                                     |
| ------------------------- | ------ | ------------------------------------------- |
| `ACT_LOCAL_TESTING`       | `true` | Identify when running in local testing mode |
| `SKIP_DOCKER_BUILDS`      | `true` | Skip Docker build steps in local testing    |
| `SKIP_LONG_RUNNING_TESTS` | `true` | Skip long-running tests in local testing    |

You can set additional environment variables by:

1. Adding them to the `.env.local` file and sourcing it before running tests
1. Adding them to the command line with `--env KEY=VALUE`

## Event Files

Sample event files are provided in the `.github/local-testing/events/` directory:

- `push.json`: Sample push event
- `pull_request.json`: Sample pull request event
- `workflow_dispatch.json`: Sample workflow dispatch event

You can customize these files or create new ones for specific testing scenarios.

## Troubleshooting

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

## Workflow Compatibility

We now use a single approach for workflow compatibility with local testing:

1. Use the `ACT_LOCAL_TESTING` environment variable to adapt behavior
1. Simplify matrix configurations when running locally
1. Skip steps that won't work in local testing

For detailed information on making workflows compatible with local testing, see the [GitHub Actions Guide](../../github-actions-guide.md).

## Additional Resources

- [act GitHub repository](https://github.com/nektos/act)
- [actionlint GitHub repository](https://github.com/rhysd/actionlint)
- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [act limitations documentation](https://github.com/nektos/act#limitations)
