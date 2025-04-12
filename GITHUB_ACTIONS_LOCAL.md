# GitHub Actions Local Testing

This document provides guidance on how to test GitHub Actions workflows locally using the industry-standard approach.

## Overview

Testing GitHub Actions workflows locally before pushing changes to GitHub offers several benefits:

- Faster development cycles
- Reduced number of commits to fix workflow issues
- Better understanding of workflow behavior
- Ability to debug issues locally

We use [nektos/act](https://github.com/nektos/act) as the standard tool for local GitHub Actions testing.

## Current Implementation Analysis

Our GitHub Actions implementation includes:

- Matrix testing across Python versions (3.11, 3.12) and operating systems
- UV package manager for dependency management
- Caching strategy for dependencies
- Separate steps for linting, type checking, and testing
- Documentation builds using MkDocs with deployment to GitHub Pages
- Semantic versioning using python-semantic-release
- Weekly scheduled security audits and maintenance checks

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [act](https://github.com/nektos/act) installed:
  - macOS/Linux: `brew install act`
  - Windows: `choco install act-cli` or `scoop install act`

## Quick Start

We provide two simple scripts for local testing:

- `github-actions-local.sh` - For bash (Unix/Linux/macOS)
- `github-actions-local.ps1` - For PowerShell (Windows)

### Basic Usage

**Bash:**

```bash
./github-actions-local.sh -w .github/workflows/ci.yml
```

**PowerShell:**

```powershell
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml
```

### Advanced Options

**Bash:**

```bash
# Test a specific job
./github-actions-local.sh -w .github/workflows/ci.yml -j build

# Test with a different event type
./github-actions-local.sh -w .github/workflows/ci.yml -e pull_request

# Enable verbose output
./github-actions-local.sh -w .github/workflows/ci.yml -v
```

**PowerShell:**

```powershell
# Test a specific job
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -JobFilter build

# Test with a different event type
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request

# Enable verbose output
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -VerboseOutput
```

## Environment Variables

| Variable            | Value                 | Purpose                                     |
| ------------------- | --------------------- | ------------------------------------------- |
| `ACT`               | `true`                | Identify when running in act                |
| `ACT_LOCAL_TESTING` | `true`                | Identify when running in local testing mode |
| `GITHUB_TOKEN`      | `local-testing-token` | Mock GitHub token for local testing         |

## Best Practices for Local Testing

### 1. Use Environment Variables for Conditional Execution

Add conditional logic to your workflows to handle local testing:

```yaml
# Skip steps that won't work locally
- name: Upload to S3
  if: ${{ env.ACT != 'true' }}
  uses: aws-actions/aws-s3-upload@v1
```

### 2. Use Versioned Actions

Always use versioned actions instead of `@master` or `@main`:

```yaml
# Good
uses: actions/checkout@v4

# Bad
uses: actions/checkout@master
```

### 3. Simplify Matrix Builds for Local Testing

Use conditional expressions to reduce matrix size during local testing:

```yaml
strategy:
  matrix:
    python-version: ${{ env.ACT == 'true' && fromJSON('["3.11"]') || fromJSON('["3.11", "3.12"]') }}
    os: ${{ env.ACT == 'true' && fromJSON('["ubuntu-latest"]') || fromJSON('["ubuntu-latest", "windows-latest", "macos-latest"]') }}
```

### 4. Handle Pull Request Events

Pull request events require more context than simple push events. To test workflows triggered by pull requests:

```bash
# Bash
./github-actions-local.sh -w .github/workflows/ci.yml -e pull_request

# PowerShell
./github-actions-local.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request
```

The scripts will automatically use the detailed template file at `.github/events/templates/pull_request.json` to provide all the necessary context without requiring GitHub authentication.

If you need to customize the pull request context (e.g., to test specific PR conditions), you can edit the file at `.github/events/pull_request.json` after it's created.

### 5. Mock External Services

For actions that interact with external services, consider adding mock implementations for local testing:

```yaml
- name: Deploy to Production
  if: ${{ env.ACT != 'true' }}
  uses: some-deploy-action@v1

- name: Mock Deployment (Local Testing)
  if: ${{ env.ACT == 'true' }}
  run: echo "Mocking deployment process for local testing"
```

### 6. Handle Docker-in-Docker Scenarios

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

## Event Templates

The scripts use template files to create event context for different trigger types. These templates are stored in `.github/events/templates/`:

- `push.json` - Template for push events
- `pull_request.json` - Template for pull request events

When you run the scripts with a specific event type, they will:

1. Check if an event file already exists at `.github/events/<event_type>.json`
1. If not, copy the template from `.github/events/templates/<event_type>.json`
1. If no template exists, create a basic event file

You can customize these templates or create new ones for other event types (e.g., `issue_comment.json`, `release.json`).

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

1. **Tests pass locally but fail in CI**

   - Check for environment differences
   - Ensure dependencies are properly specified
   - Consider adding more conditional logic based on the `ACT` environment variable

### PowerShell Script Validation

1. **VS Code Integration**:

- The repository is configured with PowerShell Script Analyzer in VS Code
- Settings are in `.vscode/settings.json` and `.vscode/PSScriptAnalyzerSettings.psd1`
- Errors and warnings will be highlighted directly in the editor

2. **Pre-commit Integration**:

- PowerShell Script Analyzer is configured in `.pre-commit-config.yaml`
- It will automatically check PowerShell scripts during commits
- To run manually: `pre-commit run powershell-script-analyzer --all-files`

3. **Common PowerShell Gotchas**:

- The `param()` block must come before any function definitions
- Use proper parameter types and default values
- Avoid using aliases in scripts (use full cmdlet names)

## Improvement Recommendations

### Code Quality Process Improvements

1. **Simplified Pre-commit Configuration**

   - Removed redundant hooks
   - Moved formatting checks to pre-commit stage
   - Ensured consistent tool availability

1. **Standardized GitHub Actions Local Testing**

   - Implemented industry-standard approach using act
   - Created simple, maintainable scripts
   - Eliminated redundant testing scripts
   - Improved documentation and best practices
   - Reduced complexity

1. **Optimized Git Hooks**

   - Configured type checking to run at both commit and push stages
   - Used pre-commit's built-in infrastructure
   - Eliminated custom scripts

### Priority Improvements

1. **Enhanced Security Testing**

   - Add SonarQube for static analysis
   - Implement GitHub's built-in secret scanning
   - Consider adding dynamic application security testing

1. **Automated Release Approval and Rollback**

   - Add an approval step using GitHub environments
   - Implement health checks after deployment
   - Create an automated rollback mechanism

1. **Documentation Preview for PRs**

   - Deploy preview versions of documentation
   - Add a comment to the PR with a link to the preview

1. **Performance Benchmarking**

   - Add performance tests for critical operations
   - Store benchmark results as artifacts
   - Compare results against previous runs

1. **Branch Protection and Code Review**

   - Require pull request reviews before merging
   - Require status checks to pass
   - Enforce PR size limits

## Conclusion

This standardized approach to local GitHub Actions testing provides a simple, reliable way to test workflows before pushing changes to GitHub. By following these best practices, you can ensure your workflows work correctly in both local and GitHub environments.
