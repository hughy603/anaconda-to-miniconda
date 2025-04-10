# Using GitHub Actions Environments for Workflow Testing

This guide explains how to set up and use GitHub Actions environments to safely test and deploy workflows.

## What are GitHub Actions Environments?

Environments in GitHub Actions provide a way to control the execution of workflows and add protection rules. They're especially useful for:

- Separating testing, staging, and production deployments
- Adding approval requirements before workflows run
- Storing environment-specific secrets
- Limiting which branches can deploy to specific environments

## Setting Up Environments

### 1. Create Environments in GitHub

1. Go to your repository on GitHub
1. Navigate to Settings > Environments
1. Click "New environment"
1. Create the following environments:
   - `testing` (for workflow testing)
   - `staging` (for pre-production validation)
   - `production` (for production deployments)

### 2. Configure Protection Rules

For each environment, configure appropriate protection rules:

#### Testing Environment

- **Deployment branches**: All branches (default)
- **Required reviewers**: None (for easy testing)
- **Wait timer**: None
- **Environment secrets**: Add any testing-specific secrets

#### Staging Environment

- **Deployment branches**: Protected branches only
- **Required reviewers**: 1 reviewer (optional)
- **Wait timer**: None
- **Environment secrets**: Add staging-specific secrets

#### Production Environment

- **Deployment branches**: `main` branch only
- **Required reviewers**: 1-2 reviewers (recommended)
- **Wait timer**: 10 minutes (optional)
- **Environment secrets**: Add production-specific secrets

## Using Environments in Workflows

### Basic Environment Usage

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    environment: production  # Specify the environment
    steps:
      - uses: actions/checkout@v4
      # Deployment steps here
```

### Multi-Environment Deployment Pipeline

```yaml
name: Deployment Pipeline

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'testing'
        type: choice
        options:
          - testing
          - staging
          - production

jobs:
  # Run tests first
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          # Your test commands here
          echo "Running tests"

  # Deploy to testing environment
  deploy-testing:
    name: Deploy to Testing
    needs: [test]
    if: success() && (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'testing' || github.event_name == 'push')
    runs-on: ubuntu-latest
    environment: testing
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to testing
        run: |
          echo "Deploying to testing environment"
          # Your deployment steps here

  # Deploy to staging environment
  deploy-staging:
    name: Deploy to Staging
    needs: [deploy-testing]
    if: success() && (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'staging' || github.event_name == 'push')
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment"
          # Your deployment steps here

  # Deploy to production environment
  deploy-production:
    name: Deploy to Production
    needs: [deploy-staging]
    if: success() && (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'production')
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          echo "Deploying to production environment"
          # Your production deployment steps here
```

## Testing Workflow Changes with Environments

### 1. Create a Feature Branch

```bash
git checkout -b workflow-test-feature
```

### 2. Modify Workflow Files

Update your workflow files to use environments.

### 3. Push Changes and Test

```bash
git add .github/workflows/
git commit -m "test: Add environment support to workflows"
git push -u origin workflow-test-feature
```

### 4. Trigger Workflow Manually

1. Go to your repository on GitHub
1. Navigate to Actions tab
1. Select your workflow
1. Click "Run workflow"
1. Select the branch and environment
1. Click "Run workflow"

### 5. Review Results

1. Check the workflow run in the Actions tab
1. If required reviewers are configured, they will receive a notification to approve the deployment
1. After approval, the workflow will continue execution

## Environment-Specific Secrets

### Adding Environment Secrets

1. Go to your repository on GitHub
1. Navigate to Settings > Environments
1. Select the environment
1. Under "Environment secrets", click "Add secret"
1. Add the secret name and value

### Using Environment Secrets in Workflows

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Use environment secret
        run: |
          echo "Using secret: ${{ secrets.DEPLOY_KEY }}"
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
```

## Best Practices

1. **Start with testing environment**: Always test workflows in the testing environment first
1. **Use branch protection rules**: Combine with environment protection for maximum security
1. **Limit production access**: Only allow specific branches and require approvals for production
1. **Use environment-specific secrets**: Don't use the same secrets across environments
1. **Document environment requirements**: Make sure team members know how to use environments
1. **Monitor deployments**: Check the deployment history in GitHub to track changes
1. **Use conditional jobs**: Make jobs conditional based on the target environment
1. **Implement rollback mechanisms**: Have a plan for rolling back failed deployments

## Troubleshooting

### Common Issues

1. **Workflow not running in environment**: Check if the branch is allowed to deploy to that environment
1. **Missing required approvals**: Ensure required reviewers have approved the deployment
1. **Secret not available**: Verify the secret is added to the correct environment
1. **Environment not found**: Make sure the environment name in the workflow matches exactly

### Debugging Tips

1. Use `if: always()` to ensure steps run even if previous steps fail
1. Add debug output with `run: echo "Debug info: ${{ toJSON(github) }}"`
1. Check the "Re-run jobs" option to retry failed jobs
