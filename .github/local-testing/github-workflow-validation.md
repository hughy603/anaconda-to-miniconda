# GitHub's Built-in Workflow Validation

This guide explains how to use GitHub's built-in workflow validation features to test your GitHub Actions workflows.

## Understanding GitHub's Workflow Validation

When you push a workflow file to GitHub, the platform automatically performs several validation checks:

1. **Syntax validation**: Checks for valid YAML syntax
1. **Workflow structure validation**: Ensures the workflow structure follows GitHub Actions specifications
1. **Action reference validation**: Verifies that referenced actions exist
1. **Expression validation**: Checks that expressions like `${{ github.ref }}` are valid

These validations happen automatically and provide immediate feedback before your workflow runs.

## Using GitHub's Workflow Validation

### Basic Validation Process

1. **Create a feature branch** for testing workflow changes
1. **Make changes** to your workflow files
1. **Push the changes** to GitHub
1. **Check for validation errors** in the GitHub UI

### Step-by-Step Guide

#### 1. Create a Feature Branch

```bash
# Create and checkout a new branch
git checkout -b workflow-test-feature

# Or use the VSCode task
# Press Ctrl+Shift+P and select "Tasks: Run Task" > "Create Feature Branch for Workflow Testing"
```

#### 2. Make Changes to Workflow Files

Edit your workflow files in `.github/workflows/` directory.

#### 3. Push Changes to GitHub

```bash
# Add and commit your changes
git add .github/workflows/
git commit -m "test: Update workflow configuration"

# Push to GitHub
git push -u origin workflow-test-feature

# Or use the VSCode task
# Press Ctrl+Shift+P and select "Tasks: Run Task" > "Push Workflow Changes for Testing"
```

#### 4. Check for Validation Errors

1. Go to your repository on GitHub
1. Navigate to the "Actions" tab
1. Look for any workflow validation errors (they'll appear as red banners)
1. If there are errors, GitHub will provide details about what's wrong

## Workflow Validation Checks

GitHub performs the following validation checks:

### 1. YAML Syntax

Ensures your workflow file is valid YAML. Common errors include:

- Incorrect indentation
- Missing colons
- Unbalanced quotes
- Invalid characters

### 2. Workflow Structure

Validates that your workflow follows the correct structure:

- Required fields (`name`, `on`, `jobs`)
- Valid event triggers
- Proper job definitions
- Valid step definitions

### 3. Action References

Checks that referenced actions exist and are properly formatted:

- Action repository exists
- Version tag or branch exists
- Required inputs are provided

### 4. Expression Syntax

Validates that expressions like `${{ github.ref }}` are properly formatted:

- Balanced braces
- Valid context references
- Proper function calls

## Testing Different Event Types

### Testing Push Events

Push events are automatically triggered when you push to a branch. To test:

1. Make changes to your workflow file
1. Push to a branch
1. Check the Actions tab to see if the workflow runs

### Testing Pull Request Events

To test pull request events:

1. Create a feature branch and push your changes
1. Create a pull request on GitHub
1. Check the Actions tab to see if the workflow runs

### Testing Scheduled Events

Scheduled events (using `cron` syntax) are harder to test. Options include:

1. Temporarily change the schedule to run more frequently
1. Use `workflow_dispatch` as an alternative trigger for testing

### Testing Manual Events (workflow_dispatch)

To test `workflow_dispatch` events:

1. Add `workflow_dispatch` to your workflow triggers
1. Push the workflow file to GitHub
1. Go to the Actions tab
1. Select your workflow
1. Click "Run workflow"
1. Select the branch and input parameters
1. Click "Run workflow" again

## Advanced Validation Techniques

### 1. Using the GitHub API

You can validate workflows programmatically using the GitHub API:

```bash
curl -X PUT \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"message":"test workflow","content":"BASE64_ENCODED_WORKFLOW"}' \
  https://api.github.com/repos/OWNER/REPO/contents/.github/workflows/test.yml
```

### 2. Using GitHub Actions to Validate Workflows

You can create a workflow that validates other workflows:

```yaml
name: Validate Workflows

on:
  pull_request:
    paths:
      - '.github/workflows/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install actionlint
        run: |
          bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)
          echo "${GITHUB_WORKSPACE}/bin" >> $GITHUB_PATH

      - name: Validate workflows
        run: |
          actionlint
```

## Troubleshooting Common Validation Errors

### Invalid Workflow File

**Error**: "Invalid workflow file"

**Solution**: Check your YAML syntax using a YAML validator or actionlint.

### Invalid Expression Syntax

**Error**: "Invalid expression syntax"

**Solution**: Check your expressions (content inside `${{ }}`) for proper syntax.

### Action Not Found

**Error**: "Action not found"

**Solution**: Verify the action exists and the reference is correct (owner/repo@ref).

### Invalid Event Configuration

**Error**: "Invalid event configuration"

**Solution**: Check that your event triggers are properly configured.

## Best Practices

1. **Use a feature branch** for testing workflow changes
1. **Validate locally first** using actionlint
1. **Start with simple workflows** and gradually add complexity
1. **Test one event type at a time**
1. **Use workflow_dispatch** for manual testing
1. **Check workflow logs** for detailed error information
1. **Use GitHub's workflow visualization** to understand job dependencies
1. **Document your testing process** for team members

## Conclusion

GitHub's built-in workflow validation provides a robust way to test your workflows without needing additional tools. By following the process outlined in this guide, you can ensure your workflows are valid and functioning correctly before merging them into your main branch.
