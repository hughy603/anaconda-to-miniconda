# GitHub Actions Testing

This directory contains tools and documentation for testing GitHub Actions workflows.

## Prerequisites

1. Install actionlint: <https://github.com/rhysd/actionlint#installation>
1. Configure GitHub repository environments (optional but recommended)

## Workflow Testing Approach

### 1. Local Validation with Actionlint

Actionlint is a static checker/linter for GitHub Actions workflow files that helps identify issues before pushing to GitHub.

```bash
# Validate a specific workflow
actionlint .github/workflows/ci.yml

# Validate all workflows
actionlint .github/workflows/*.yml
```

### 2. GitHub's Built-in Workflow Validation

GitHub automatically validates workflow syntax when you push changes. This is the most reliable way to test workflows.

1. Create a feature branch for testing:

   ```bash
   git checkout -b workflow-test-feature
   ```

1. Make your changes to workflow files

1. Push the changes to trigger validation:

   ```bash
   git add .github/workflows/
   git commit -m "test: Test workflow changes"
   git push -u origin workflow-test-feature
   ```

1. Check the Actions tab in your GitHub repository to see if the workflows run correctly

### 3. Using GitHub Actions Environments for Testing

GitHub Actions environments provide a way to control workflow execution and add protection rules.

#### Setting Up Environments

1. Go to your repository on GitHub
1. Navigate to Settings > Environments
1. Click "New environment"
1. Create environments like:
   - `testing` (for workflow testing)
   - `staging` (for pre-production)
   - `production` (for production deployments)

#### Environment Protection Rules

For each environment, you can configure:

- Required reviewers
- Wait timer
- Deployment branches
- Environment secrets

#### Using Environments in Workflows

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy-testing:
    name: Deploy to Testing
    runs-on: ubuntu-latest
    environment: testing
    steps:
      - uses: actions/checkout@v4
      # Your deployment steps here

  deploy-production:
    name: Deploy to Production
    needs: [deploy-testing]
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      # Your production deployment steps here
```

## Best Practices

1. **Always validate workflows locally** with actionlint before pushing
1. **Use feature branches** for testing workflow changes
1. **Set up environments** with protection rules for sensitive workflows
1. **Use environment secrets** instead of repository secrets when possible
1. **Add required reviewers** to production environments
1. **Test workflows with different event types** (push, pull_request, workflow_dispatch)
1. **Use conditional jobs** that depend on previous job results
1. **Monitor workflow runs** in the Actions tab to identify issues

## VSCode Integration

This repository includes VSCode tasks for workflow validation and testing. Press `Ctrl+Shift+P` and type "Tasks: Run Task" to see available tasks:

- Validate Workflow with Actionlint
- Validate All Workflows
- Create Feature Branch for Workflow Testing
- Push Workflow Changes for Testing
