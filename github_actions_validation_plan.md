# GitHub Actions Workflow Validation Python Package

This document outlines the plan for replacing the PowerShell GitHub Actions validation with a Python implementation that provides better error handling and follows industry best practices.

## 1. Package Structure

The package will be implemented as a separate module under the `src/` directory:

```
src/
├── conda_forge_converter/  (existing package)
└── github_actions_validator/  (new package)
    ├── __init__.py
    ├── _version.py
    ├── cli.py
    ├── config.py
    ├── discovery.py
    ├── error_handling.py
    ├── validators/
    │   ├── __init__.py
    │   ├── syntax.py
    │   └── execution.py
    ├── runners/
    │   ├── __init__.py
    │   ├── act.py
    │   └── actionlint.py
    └── utils.py
```

This structure allows for:

1. Clear separation from the existing conda_forge_converter package
1. Simple extraction into a standalone package in the future
1. Clear separation of concerns within the package

## 2. Package Dependencies

We'll need to add the following dependencies to the pyproject.toml file:

```toml
[project]
dependencies = [
    # Existing dependencies
    "pyyaml>=6.0.1",
    "typing_extensions>=4.10.0",
    # New dependencies for github_actions_validator
    "click>=8.1.0",  # For CLI interface
    "rich>=13.0.0",  # For beautiful terminal output
]

[project.scripts]
conda-forge-converter = "conda_forge_converter.cli:main"
validate-github-workflows = "github_actions_validator.cli:main"
```

These are industry-standard libraries that will help us implement a robust solution.

## 3. Component Design

### 3.1 Core Components

#### CLI Module (`cli.py`)

```python
import click
from rich.console import Console
from pathlib import Path
from typing import List, Optional

from .config import Config
from .discovery import find_workflows
from .validators import validate_workflow, validate_workflows


@click.command()
@click.option(
    "--changed-only", is_flag=True, help="Only validate workflows that have changed"
)
@click.option("--parallel", is_flag=True, help="Run validations in parallel")
@click.option("--max-parallel", default=3, help="Maximum number of parallel jobs")
@click.option(
    "--secrets-file", default=".github/local-secrets.json", help="Path to secrets file"
)
@click.option("--cache-path", default="./.act-cache", help="Path to cache directory")
@click.option("--custom-image", default="", help="Use custom Docker image")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--dry-run", is_flag=True, help="List workflows without running them")
@click.option("--skip-lint", is_flag=True, help="Skip actionlint validation")
@click.option("--default-event", default="push", help="Default event type")
@click.option("--workflow-file", default="", help="Specific workflow file to validate")
def main(
    changed_only: bool,
    parallel: bool,
    max_parallel: int,
    secrets_file: str,
    cache_path: str,
    custom_image: str,
    verbose: bool,
    dry_run: bool,
    skip_lint: bool,
    default_event: str,
    workflow_file: str,
) -> int:
    """Validate GitHub Actions workflows locally."""

    console = Console()
    config = Config(
        changed_only=changed_only,
        parallel=parallel,
        max_parallel=max_parallel,
        secrets_file=secrets_file,
        cache_path=cache_path,
        custom_image=custom_image,
        verbose=verbose,
        dry_run=dry_run,
        skip_lint=skip_lint,
        default_event=default_event,
    )

    # Main validation logic
    # ...

    return 0  # Success
```

#### Configuration Module (`config.py`)

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class Config:
    """Configuration for GitHub Actions workflow validation."""

    changed_only: bool = False
    parallel: bool = False
    max_parallel: int = 3
    secrets_file: str = ".github/local-secrets.json"
    cache_path: str = "./.act-cache"
    custom_image: str = ""
    verbose: bool = False
    dry_run: bool = False
    skip_lint: bool = False
    default_event: str = "push"
    workflow_events: Dict[str, str] = None

    def __post_init__(self):
        if self.workflow_events is None:
            self.workflow_events = {
                "ci.yml": "push",
                "docs.yml": "push",
                "release.yml": "push",
                "benchmark.yml": "push",
                "maintenance.yml": "schedule",
                "security-scan.yml": "push",
                "validate-workflows.yml": "pull_request",
                "*": self.default_event,  # Default for any other workflow
            }
```

#### Workflow Discovery Module (`discovery.py`)

```python
import subprocess
from pathlib import Path
from typing import List, Optional


def find_workflows(
    changed_only: bool = False, workflow_file: Optional[str] = None
) -> List[Path]:
    """Find GitHub Actions workflow files to validate."""

    if workflow_file:
        path = Path(workflow_file)
        if path.exists():
            return [path]
        else:
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")

    if changed_only:
        # Get changed workflow files using git
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True
        )
        changed_files = [
            Path(file)
            for file in result.stdout.splitlines()
            if file.startswith(".github/workflows/")
            and file.endswith((".yml", ".yaml"))
        ]
        return changed_files

    # Get all workflow files
    return list(Path(".github/workflows").glob("*.yml")) + list(
        Path(".github/workflows").glob("*.yaml")
    )
```

### 3.2 Error Handling

The error handling module is a key component that will significantly improve the user experience by providing detailed, actionable error messages.

#### Error Handling Module (`error_handling.py`)

```python
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax


class ErrorSeverity(Enum):
    """Severity levels for validation errors."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class ValidationError:
    """Represents a validation error with context and suggestions."""

    message: str
    severity: ErrorSeverity
    workflow_file: Optional[str] = None
    job_name: Optional[str] = None
    line_number: Optional[int] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None


class ErrorReporter:
    """Handles error reporting and suggestions for workflow validation."""

    def __init__(self, console: Console):
        self.console = console
        self.error_patterns = {
            r"No such file or directory": "Check if all referenced files exist in the repository",
            r"Unknown action": "Make sure the action is publicly available or included in the repository",
            r"Invalid workflow file": "Validate the YAML syntax of your workflow file",
            r"not found": "Ensure the referenced resource exists and is accessible",
            r"permission denied": "Check file permissions or if you need elevated privileges",
            r"Could not find a version": "The specified package version may not exist or be available in the current environment",
            r"Could not find any stages to run": "This is likely due to event trigger mismatch. Check that your workflow triggers match the event type you're testing with.",
            r"exit status \d+": "The action failed with a non-zero exit code. Check the action's logs for more details.",
        }

    def format_error(
        self,
        error_message: str,
        workflow_name: Optional[str] = None,
        job_name: Optional[str] = None,
    ) -> ValidationError:
        """Format error message with helpful suggestions."""

        severity = ErrorSeverity.ERROR
        suggestion = None

        # Check for known error patterns and provide suggestions
        for pattern, hint in self.error_patterns.items():
            if re.search(pattern, error_message):
                suggestion = hint
                break

        return ValidationError(
            message=error_message,
            severity=severity,
            workflow_file=workflow_name,
            job_name=job_name,
            suggestion=suggestion,
        )

    def report_error(self, error: ValidationError):
        """Report an error with rich formatting."""

        # Determine color based on severity
        color = {
            ErrorSeverity.INFO: "blue",
            ErrorSeverity.WARNING: "yellow",
            ErrorSeverity.ERROR: "red",
            ErrorSeverity.CRITICAL: "red bold",
        }[error.severity]

        # Build error message
        title = f"Error in {error.workflow_file}"
        if error.job_name:
            title += f" (job: {error.job_name})"

        content = [error.message]

        if error.context:
            syntax = Syntax(error.context, "yaml", theme="monokai", line_numbers=True)
            content.append("\nContext:")
            content.append(syntax)

        if error.suggestion:
            content.append(f"\n[bold]Suggestion:[/bold] {error.suggestion}")

        # Display the error
        self.console.print(
            Panel("\n".join(str(c) for c in content), title=title, border_style=color)
        )
```

### 3.3 Validator Components

#### Syntax Validator (`validators/syntax.py`)

```python
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from ..error_handling import ErrorReporter, ValidationError, ErrorSeverity


def validate_syntax(
    workflow_file: Path, error_reporter: ErrorReporter
) -> Tuple[bool, List[ValidationError]]:
    """Validate workflow syntax using actionlint."""

    errors = []

    # Run actionlint
    result = subprocess.run(
        ["pre-commit", "run", "actionlint", "--files", str(workflow_file)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Parse actionlint output for detailed error information
        for line in result.stderr.splitlines() + result.stdout.splitlines():
            if line.strip() and "error" in line.lower():
                error = error_reporter.format_error(
                    error_message=line, workflow_name=workflow_file.name
                )
                errors.append(error)

    return len(errors) == 0, errors
```

#### Execution Validator (`validators/execution.py`)

```python
import json
import re
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..error_handling import ErrorReporter, ValidationError, ErrorSeverity
from ..config import Config
from ..runners.act import ActRunner


def extract_jobs(workflow_file: Path) -> List[str]:
    """Extract job names from a workflow file using proper YAML parsing."""

    with open(workflow_file, "r") as f:
        try:
            workflow = yaml.safe_load(f)

            # Check if the workflow has a jobs section
            if not workflow or "jobs" not in workflow:
                return []

            # Extract job names
            return list(workflow["jobs"].keys())
        except yaml.YAMLError as e:
            # If YAML parsing fails, return empty list
            # The syntax validator will catch this error
            return []


def validate_execution(
    workflow_file: Path, config: Config, error_reporter: ErrorReporter
) -> Tuple[bool, List[ValidationError]]:
    """Validate workflow execution using act."""

    errors = []
    act_runner = ActRunner(config)

    # Extract jobs from the workflow
    jobs = extract_jobs(workflow_file)

    if not jobs:
        # No jobs found, validate the entire workflow
        success, error = act_runner.run_workflow(workflow_file)
        if not success:
            errors.append(error)
        return success, errors

    # Validate each job individually
    all_jobs_success = True
    for job in jobs:
        success, error = act_runner.run_workflow(workflow_file, job_filter=job)
        if not success:
            all_jobs_success = False
            errors.append(error)

    return all_jobs_success, errors
```

### 3.4 Runner Components

#### Act Runner (`runners/act.py`)

```python
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import Config
from ..error_handling import ValidationError, ErrorSeverity


class ActRunner:
    """Handles running GitHub Actions workflows with act."""

    def __init__(self, config: Config):
        self.config = config

    def prepare_event_file(self, event_type: str) -> Path:
        """Prepare event file for act."""

        event_file = Path(f".github/events/{event_type}.json")

        # Create event directory if it doesn't exist
        event_file.parent.mkdir(parents=True, exist_ok=True)

        # Create event file if it doesn't exist
        if not event_file.exists():
            # Basic event data
            event_data = {
                "ref": "refs/heads/master",
                "repository": {
                    "name": "anaconda-to-miniconda",
                    "full_name": "ricea/anaconda-to-miniconda",
                    "owner": {"name": "ricea"},
                },
            }

            # Write event file
            with open(event_file, "w") as f:
                json.dump(event_data, f, indent=4)

        return event_file

    def build_act_command(
        self,
        workflow_file: Path,
        event_type: str = "push",
        job_filter: Optional[str] = None,
    ) -> List[str]:
        """Build act command with appropriate options."""

        # Normalize paths to use forward slashes
        normalized_workflow_file = str(workflow_file).replace("\\", "/")

        # Prepare event file
        event_file = self.prepare_event_file(event_type)
        normalized_event_file = str(event_file).replace("\\", "/")

        # Build command
        cmd = ["act", "-W", normalized_workflow_file, "-e", normalized_event_file]

        # Add job filter if provided
        if job_filter:
            cmd.extend(["--job", job_filter])

        # Add platform mapping
        cmd.extend(["-P", "ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"])

        # Add cache path
        if os.path.exists(self.config.cache_path):
            cmd.extend(["--action-cache-path", self.config.cache_path])

        # Add environment variables
        cmd.extend(["--env", "ACT=true", "--env", "ACT_LOCAL_TESTING=true"])

        # Add secrets
        cmd.extend(["-s", "ACT=true", "-s", "ACT_LOCAL_TESTING=true"])

        # Add custom image if specified
        if self.config.custom_image:
            cmd.extend(["-P", self.config.custom_image])

        # Add secrets file if it exists
        if os.path.exists(self.config.secrets_file):
            cmd.extend(["--secret-file", self.config.secrets_file])

        # Add verbose flag if specified
        if self.config.verbose:
            cmd.append("--verbose")

        return cmd

    def run_workflow(
        self,
        workflow_file: Path,
        event_type: str = "push",
        job_filter: Optional[str] = None,
    ) -> Tuple[bool, Optional[ValidationError]]:
        """Run workflow with act and return success status and any error."""

        # Build command
        cmd = self.build_act_command(workflow_file, event_type, job_filter)

        # Run command
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check for "Could not find any stages to run" which is a special case
        if (
            "Could not find any stages to run" in result.stdout
            or "Could not find any stages to run" in result.stderr
        ):
            # This is not necessarily an error, but we should report it
            return True, ValidationError(
                message="Could not find any stages to run. This is likely due to event trigger mismatch.",
                severity=ErrorSeverity.WARNING,
                workflow_file=str(workflow_file),
                job_name=job_filter,
                suggestion="Check that your workflow triggers match the event type you're testing with.",
            )

        # Check for errors
        if result.returncode != 0:
            # Extract error message
            error_message = result.stderr if result.stderr else result.stdout

            # Create validation error
            return False, ValidationError(
                message=f"Workflow execution failed with exit code {result.returncode}",
                severity=ErrorSeverity.ERROR,
                workflow_file=str(workflow_file),
                job_name=job_filter,
                context=(
                    error_message[:500] if len(error_message) > 500 else error_message
                ),  # Limit context size
                suggestion="Check the error message for details on what went wrong.",
            )

        return True, None
```

## 4. Integration with Main Project

### 4.1 Entry Point

We'll add a new entry point in pyproject.toml:

```toml
[project.scripts]
conda-forge-converter = "conda_forge_converter.cli:main"
validate-github-workflows = "github_actions_validator.cli:main"
```

### 4.2 Package Initialization

In `src/github_actions_validator/__init__.py`:

```python
"""GitHub Actions workflow validation package."""

from ._version import __version__

__all__ = ["__version__"]
```

In `src/github_actions_validator/_version.py`:

```python
"""Version information."""

__version__ = "0.1.0"
```

## 5. Error Handling Improvements

The Python implementation will significantly improve error handling:

### 5.1 Structured Error Classification

Errors will be categorized by type and severity:

```python
class ErrorSeverity(Enum):
    INFO = auto()  # Informational messages
    WARNING = auto()  # Potential issues that don't prevent execution
    ERROR = auto()  # Issues that prevent successful execution
    CRITICAL = auto()  # Severe issues that require immediate attention
```

### 5.2 Contextual Error Messages

Errors will include context about where they occurred:

```
Error in ci.yml (job: build)
--------------------------
Workflow execution failed with exit code 1

Context:
1 | Error: Process completed with exit code 1.
2 | ##[error] Process completed with exit code 1.
3 | Error: Unknown action: 'actions/setup-pythonx@v4'
4 | Did you mean 'actions/setup-python@v4'?

Suggestion: Make sure the action is publicly available or included in the repository
```

### 5.3 Intelligent Error Analysis

The system will analyze output from act and actionlint to extract meaningful information:

```python
def analyze_act_output(output: str) -> List[ValidationError]:
    """Analyze act output for errors and warnings."""

    errors = []

    # Look for common error patterns
    if "Unknown action" in output:
        # Extract the action name
        match = re.search(r"Unknown action: '([^']+)'", output)
        if match:
            action_name = match.group(1)
            errors.append(
                ValidationError(
                    message=f"Unknown action: '{action_name}'",
                    severity=ErrorSeverity.ERROR,
                    context=output,
                    suggestion=f"Check that the action name is correct and publicly available.",
                )
            )

    # More error patterns...

    return errors
```

### 5.4 Actionable Suggestions

For each error, the system will provide specific suggestions for fixing it:

```
Error: Unknown action: 'actions/setup-pythonx@v4'
Suggestion: The action name appears to be misspelled. Did you mean 'actions/setup-python@v4'?
```

### 5.5 Visual Error Reporting

Errors will be displayed with rich formatting to highlight important information:

```
╭─ Error in ci.yml (job: build) ──────────────────────────────────────╮
│ Workflow execution failed with exit code 1                          │
│                                                                     │
│ Context:                                                            │
│ 1 │ Error: Process completed with exit code 1.                      │
│ 2 │ ##[error] Process completed with exit code 1.                   │
│ 3 │ Error: Unknown action: 'actions/setup-pythonx@v4'               │
│ 4 │ Did you mean 'actions/setup-python@v4'?                         │
│                                                                     │
│ Suggestion: Make sure the action is publicly available or included  │
│ in the repository                                                   │
╰─────────────────────────────────────────────────────────────────────╯
```

## 6. Implementation Phases

I recommend implementing this solution in phases:

### Phase 1: Core Functionality

- Basic CLI interface
- Workflow discovery
- Simple validation with act
- Basic error reporting

### Phase 2: Enhanced Validation

- Proper YAML parsing
- Job extraction and individual job testing
- Parallel execution

### Phase 3: Advanced Error Handling

- Detailed error analysis
- Suggestions for fixes
- Rich terminal output

### Phase 4: Additional Features

- Support for matrix jobs
- Custom event types
- Performance optimizations

## 7. Testing Strategy

The implementation should include:

1. **Unit Tests**

   - Test individual components (YAML parsing, job extraction, etc.)
   - Mock external dependencies (act, actionlint)

1. **Integration Tests**

   - Test the entire validation process
   - Use sample workflows with known issues

1. **Comparison Tests**

   - Compare results with the PowerShell implementation
   - Ensure all features are properly implemented

## 8. Documentation

The Python implementation will include:

1. **Code Documentation**

   - Docstrings for all functions and classes
   - Type hints for better IDE support

1. **User Documentation**

   - README with usage examples
   - Detailed explanation of options
   - Troubleshooting guide

1. **Developer Documentation**

   - Architecture overview
   - Extension points
   - Contribution guidelines

## 9. Future Extraction as Standalone Package

The modular design will make it easy to extract this functionality into a standalone package in the future:

1. Copy the `github_actions_validator` directory to a new repository
1. Update imports if necessary
1. Create a new pyproject.toml file
1. Publish as a standalone package
