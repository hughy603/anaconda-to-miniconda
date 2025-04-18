# GitHub Actions Workflow Validator

A Python package for validating GitHub Actions workflows locally with improved error handling and reporting.

## Features

- Validate GitHub Actions workflow syntax using actionlint
- Run workflows locally using act
- Extract and validate individual jobs
- Detailed error reporting with suggestions for fixes
- Support for parallel validation
- Support for validating only changed workflows

## Installation

This package is included as part of the conda-forge-converter project. To install it, you can use pip:

```bash
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Validate all workflows
validate-github-workflows

# Validate only changed workflows
validate-github-workflows --changed-only

# Validate a specific workflow
validate-github-workflows --workflow-file .github/workflows/ci.yml

# Run validations in parallel
validate-github-workflows --parallel --max-parallel 3

# Skip actionlint validation
validate-github-workflows --skip-lint

# Dry run (list workflows without running them)
validate-github-workflows --dry-run

# Use custom Docker image
validate-github-workflows --custom-image "ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"

# Use custom secrets file
validate-github-workflows --secrets-file .github/local-secrets.json
```

### Python API

```python
from github_actions_validator.config import Config
from github_actions_validator.discovery import find_workflows
from github_actions_validator.error_handling import ErrorReporter
from github_actions_validator.validators.execution import validate_workflows

# Create configuration
config = Config(
    changed_only=True, parallel=True, max_parallel=3, skip_lint=False, dry_run=False
)

# Find workflows
workflow_files = find_workflows(changed_only=config.changed_only)

# Create error reporter
error_reporter = ErrorReporter()

# Validate workflows
success, errors = validate_workflows(workflow_files, config, error_reporter)

# Report errors
for workflow_file, workflow_errors in errors.items():
    for error in workflow_errors:
        error_reporter.report_error(error)
```

## Requirements

- Python 3.11 or higher
- Docker (for running workflows locally)
- act (for running workflows locally)
- actionlint (for syntax validation)
- pre-commit (for running actionlint)

## Error Handling

The package provides detailed error reporting with suggestions for fixing common issues. For example:

```
Error in ci.yml (job: build)
--------------------------
Workflow execution failed with exit code 1

Context:
Error: Unknown action: 'actions/setup-pythonx@v4'
Did you mean 'actions/setup-python@v4'?

Suggestion: Make sure the action is publicly available or included in the repository
```

## Documentation

For more detailed documentation, see:

- [Matrix Jobs](docs/matrix_jobs.md): How to validate workflows with matrix jobs
- [Troubleshooting](docs/troubleshooting.md): Common issues and solutions
- [Contributing](CONTRIBUTING.md): Guidelines for contributing to the project

## License

This package is licensed under the MIT License.
