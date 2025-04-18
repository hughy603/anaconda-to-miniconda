#!/usr/bin/env python3
"""Example script demonstrating how to use the GitHub Actions workflow validator.

This script shows how to validate GitHub Actions workflows programmatically
using the GitHub Actions validator package.
"""

import sys
from pathlib import Path

from rich.console import Console

# Add the parent directory to the path so we can import the package
sys.path.append(str(Path(__file__).parent.parent.parent))
from github_actions_validator.config import ValidationConfig
from github_actions_validator.discovery import find_workflows
from github_actions_validator.validators.execution import validate_all_execution


def main() -> int | None:
    """Validate GitHub Actions workflows."""
    # Create a Rich console for formatted output
    console = Console()

    # Create configuration
    config = ValidationConfig.create(
        changed_only=False,  # Validate all workflows
        skip_lint=False,  # Don't skip actionlint validation
        dry_run=False,  # Actually run the validations
        verbose=True,  # Enable verbose output
    )

    try:
        # Find workflows to validate
        console.print("[bold]Finding workflows to validate...[/bold]")
        workflow_files = find_workflows()

        if not workflow_files:
            console.print("[yellow]No workflows found.[/yellow]")
            return 0

        console.print(f"[green]Found {len(workflow_files)} workflow files:[/green]")
        for workflow_file in workflow_files:
            console.print(f"  - {workflow_file}")

        # Validate workflows
        console.print("\n[bold]Validating workflows...[/bold]")
        success, errors = validate_all_execution(workflow_files, config)

        # Print summary
        if success:
            console.print("\n[bold green]✅ All workflows validated successfully![/bold green]")
        else:
            console.print("\n[bold red]❌ One or more workflows failed validation.[/bold red]")

            # Count errors
            error_count = len(errors)
            console.print(f"Found {error_count} errors.")

        return 0 if success else 1

    except Exception as e:
        console.print(f"[bold red]Error: {e!s}[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
