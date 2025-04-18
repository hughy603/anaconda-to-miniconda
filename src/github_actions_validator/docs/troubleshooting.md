# Troubleshooting Guide

This guide helps you troubleshoot common issues when using the GitHub Actions validator.

## Common Issues

### Docker Not Running

**Symptom**: You see an error like "Cannot connect to the Docker daemon" or "Docker daemon is not running".

**Solution**:

1. Make sure Docker Desktop is installed and running
1. Check that your user has permission to access Docker
1. On Linux, you might need to start the Docker service:
   ```bash
   sudo systemctl start docker
   ```

### Act Not Installed

**Symptom**: You see an error like "act: command not found" or "act is not installed".

**Solution**:

1. Install act using the instructions from the [act repository](https://github.com/nektos/act#installation)
1. Make sure act is in your PATH
1. Verify the installation by running:
   ```bash
   act --version
   ```

### Actionlint Not Installed

**Symptom**: You see an error like "actionlint: command not found" or "actionlint is not installed".

**Solution**:

1. Install actionlint using the instructions from the [actionlint repository](https://github.com/rhysd/actionlint#installation)
1. Make sure actionlint is in your PATH
1. Verify the installation by running:
   ```bash
   actionlint --version
   ```

### Pre-commit Not Installed

**Symptom**: You see an error like "pre-commit: command not found" or "pre-commit is not installed".

**Solution**:

1. Install pre-commit using pip:
   ```bash
   pip install pre-commit
   ```
1. Verify the installation by running:
   ```bash
   pre-commit --version
   ```

### Could Not Find Any Stages to Run

**Symptom**: You see a message like "Could not find any stages to run" when running a workflow.

**Solution**:

1. Check that the workflow is triggered by the event type you're using
1. Make sure the workflow file is valid YAML
1. Try using a different event type:
   ```bash
   validate-github-workflows --workflow-file .github/workflows/your-workflow.yml --default-event pull_request
   ```
1. Check if the workflow has conditional triggers that might be preventing it from running

### Unknown Action

**Symptom**: You see an error like "Unknown action: 'actions/setup-pythonx@v4'".

**Solution**:

1. Check the action name for typos
1. Make sure the action exists and is publicly available
1. Check the version of the action
1. If it's a custom action, make sure it's available in your repository

### Permission Denied

**Symptom**: You see an error like "permission denied" when running a workflow.

**Solution**:

1. Check file permissions for the workflow file and any scripts it runs
1. Make sure you have permission to access Docker
1. On Linux, you might need to run with sudo or add your user to the docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```
   (Log out and back in for this to take effect)

### Workflow Runs Locally But Fails on GitHub

**Symptom**: Your workflow runs successfully with the validator but fails when run on GitHub.

**Solution**:

1. Check for environment differences between your local machine and GitHub
1. Make sure all required secrets are properly configured
1. Check if the workflow uses GitHub-specific features that might not be available locally
1. Try running with the `--verbose` flag to get more information:
   ```bash
   validate-github-workflows --workflow-file .github/workflows/your-workflow.yml --verbose
   ```

### Python Package Not Found

**Symptom**: You see an error like "No module named 'github_actions_validator'".

**Solution**:

1. Make sure the package is installed:
   ```bash
   pip install -e .
   ```
1. Check your Python path:
   ```bash
   python -c "import sys; print(sys.path)"
   ```
1. Make sure you're using the correct Python interpreter

### Validation Takes Too Long

**Symptom**: Validation takes a long time to complete, especially for workflows with many jobs.

**Solution**:

1. Use the `--parallel` flag to run validations in parallel:
   ```bash
   validate-github-workflows --parallel --max-parallel 4
   ```
1. Use the `--changed-only` flag to validate only changed workflows:
   ```bash
   validate-github-workflows --changed-only
   ```
1. Use the `--skip-lint` flag to skip actionlint validation:
   ```bash
   validate-github-workflows --skip-lint
   ```
1. Validate specific workflows instead of all workflows:
   ```bash
   validate-github-workflows --workflow-file .github/workflows/your-workflow.yml
   ```

## Advanced Troubleshooting

### Debugging Act

To get more information about what act is doing, you can use the `--verbose` flag:

```bash
validate-github-workflows --verbose
```

You can also run act directly with the `-v` flag:

```bash
act -v -W .github/workflows/your-workflow.yml -e .github/events/push.json
```

### Debugging Actionlint

To get more information about what actionlint is finding, you can run it directly:

```bash
actionlint .github/workflows/your-workflow.yml
```

### Checking Event Files

The validator creates event files in the `.github/events` directory. You can check these files to see what events are being used:

```bash
cat .github/events/push.json
```

You can also create custom event files for specific scenarios.

### Checking Docker Images

Act uses Docker images to run workflows. You can check what images are available:

```bash
docker images
```

If you're having issues with a specific platform, you can try using a custom image:

```bash
validate-github-workflows --custom-image "ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"
```

## Getting Help

If you're still having issues, you can:

1. Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
1. Check the [act repository](https://github.com/nektos/act) for issues and solutions
1. Check the [actionlint repository](https://github.com/rhysd/actionlint) for issues and solutions
1. Open an issue in the GitHub repository for this package

## Contributing

If you find a solution to an issue that's not covered in this guide, please consider contributing to the documentation by opening a pull request.
