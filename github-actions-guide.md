# GitHub Actions Guide

> **Note:** This guide has been simplified. For comprehensive information, see the [GitHub Actions section in the README.md](README.md#github-actions).

## Local Testing Quick Reference

### Bash Commands

```bash
# Test a workflow (defaults to push event)
.github/local-testing/local-test.sh .github/workflows/ci.yml

# Test with a specific Python version
.github/local-testing/local-test.sh .github/workflows/ci.yml push "" python-version=3.11

# Validate a workflow file
.github/local-testing/validate-workflow.sh .github/workflows/ci.yml
```

### PowerShell Commands

```powershell
# Test a workflow
.github/local-testing/local-test.ps1 -WorkflowFile .github/workflows/ci.yml

# Test with a specific Python version
.github/local-testing/local-test.ps1 -WorkflowFile .github/workflows/ci.yml -PythonVersion 3.11
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [act](https://github.com/nektos/act) installed

## Environment Variables

| Variable                  | Value  | Purpose                                     |
| ------------------------- | ------ | ------------------------------------------- |
| `ACT_LOCAL_TESTING`       | `true` | Identify when running in local testing mode |
| `SKIP_DOCKER_BUILDS`      | `true` | Skip Docker build steps in local testing    |
| `SKIP_LONG_RUNNING_TESTS` | `true` | Skip long-running tests in local testing    |

## Troubleshooting

1. **Docker not running**

   - Start Docker Desktop and try again

1. **"Unknown action" error**

   - For composite actions, use relative paths: `./.github/actions/my-action`

1. **Tests pass locally but fail in CI**

   - Check for environment differences
   - Ensure dependencies are properly specified
