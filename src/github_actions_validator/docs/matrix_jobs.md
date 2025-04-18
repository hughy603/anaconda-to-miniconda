# Validating Matrix Jobs

GitHub Actions workflows often use matrix strategies to run jobs with different configurations. This document explains how to validate workflows with matrix jobs using the GitHub Actions validator.

## Understanding Matrix Jobs

Matrix jobs in GitHub Actions allow you to run a job multiple times with different configurations. For example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Run tests
        run: python -m pytest
```

This job will run 12 times (4 Python versions × 3 operating systems).

## Validating Matrix Jobs

The GitHub Actions validator can validate workflows with matrix jobs in two ways:

### 1. Validating the Entire Workflow

When you validate the entire workflow, the validator will check the syntax of the workflow file and run the workflow using act. However, act has limitations when it comes to matrix jobs:

- It will only run one combination of the matrix by default
- It may not fully expand all matrix combinations

To validate the entire workflow:

```bash
validate-github-workflows --workflow-file .github/workflows/matrix.yml
```

### 2. Validating Specific Matrix Combinations

To validate specific matrix combinations, you need to modify the event file to specify the matrix combination you want to test. The GitHub Actions validator doesn't currently provide built-in support for this, but you can do it manually:

1. Create a custom event file for the matrix combination:

```json
{
  "ref": "refs/heads/master",
  "repository": {
    "name": "your-repo",
    "full_name": "your-username/your-repo",
    "owner": {
      "name": "your-username"
    }
  },
  "inputs": {
    "python-version": "3.11",
    "os": "ubuntu-latest"
  }
}
```

2. Run act with the custom event file:

```bash
act -W .github/workflows/matrix.yml -e .github/events/custom-matrix.json --job test
```

## Future Enhancements

In future versions of the GitHub Actions validator, we plan to add built-in support for validating specific matrix combinations:

```bash
# Not yet implemented
validate-github-workflows --workflow-file .github/workflows/matrix.yml --matrix "python-version=3.11,os=ubuntu-latest"
```

## Workaround for Matrix Job Validation

Until built-in support is added, you can use the following approach to validate matrix jobs:

1. Create a script that generates event files for each matrix combination you want to test
1. Run the validator for each event file

Here's an example script:

```python
#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

# Define the matrix combinations to test
matrix_combinations = [
    {"python-version": "3.11", "os": "ubuntu-latest"},
    {"python-version": "3.8", "os": "windows-latest"},
    # Add more combinations as needed
]

# Create the events directory if it doesn't exist
events_dir = Path(".github/events")
events_dir.mkdir(parents=True, exist_ok=True)

# Workflow file to test
workflow_file = ".github/workflows/matrix.yml"

# Test each matrix combination
for i, combination in enumerate(matrix_combinations):
    # Create the event file
    event_file = events_dir / f"matrix-{i}.json"
    event_data = {
        "ref": "refs/heads/master",
        "repository": {
            "name": "your-repo",
            "full_name": "your-username/your-repo",
            "owner": {"name": "your-username"},
        },
        "inputs": combination,
    }

    with open(event_file, "w") as f:
        json.dump(event_data, f, indent=2)

    # Run act with the event file
    cmd = ["act", "-W", workflow_file, "-e", str(event_file), "--job", "test"]

    print(f"Testing matrix combination: {combination}")
    subprocess.run(cmd)
```

## Best Practices for Matrix Jobs

When using matrix jobs in your workflows, consider the following best practices:

1. **Limit the number of combinations**: Too many combinations can slow down your CI/CD pipeline.
1. **Use include/exclude**: Use the `include` and `exclude` options to add or remove specific combinations.
1. **Test locally**: Test your matrix jobs locally before pushing to GitHub.
1. **Use fail-fast**: Set `fail-fast: true` to cancel all in-progress jobs if any job fails.
1. **Use conditional execution**: Use `if` conditions to skip certain steps based on matrix values.

## Conclusion

While the GitHub Actions validator doesn't currently provide built-in support for validating specific matrix combinations, you can use the workarounds described in this document to validate your matrix jobs. We plan to add better support for matrix jobs in future versions of the validator.
