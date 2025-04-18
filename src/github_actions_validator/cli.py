"""Command-line interface for GitHub Actions validation.

This module provides a command-line interface for validating GitHub Actions
workflows using Click for command groups and Pydantic for configuration.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import click
from rich.console import Console

from .config import ValidationConfig
from .discovery import find_workflows
from .errors import ErrorReporter, ExecutionError, SyntaxError
from .validators import validate_all_execution, validate_all_syntax

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GitHub Actions validation tools."""
    pass


@cli.command()
@click.option("--changed-only", is_flag=True, help="Only validate workflows that have changed")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--dry-run", is_flag=True, help="List workflows without running them")
@click.option("--skip-lint", is_flag=True, help="Skip actionlint validation")
@click.option("--default-event", default="push", help="Default event type")
@click.option("--workflow-file", default="", help="Specific workflow file to validate")
@click.option("--config-file", default=None, help="Path to configuration file")
def validate(
    changed_only: bool,
    verbose: bool,
    dry_run: bool,
    skip_lint: bool,
    default_event: str,
    workflow_file: str,
    config_file: str | None,
):
    """Validate GitHub Actions workflows.

    This command validates GitHub Actions workflows using actionlint for syntax
    validation and act for execution validation.

    Examples:
        # Validate all workflows
        validate-github-workflows validate

        # Validate a specific workflow
        validate-github-workflows validate --workflow-file .github/workflows/docs.yml

        # Validate only changed workflows
        validate-github-workflows validate --changed-only
    """
    # Get configuration with precedence: CLI > env > file > defaults
    config = ValidationConfig.create(
        config_file=config_file,
        changed_only=changed_only,
        verbose=verbose,
        dry_run=dry_run,
        skip_lint=skip_lint,
        default_event=default_event,
        workflow_file=workflow_file,
    )

    # Create error reporter
    reporter = ErrorReporter(verbose=config.verbose)

    # Find workflows to validate
    if config.workflow_file:
        workflow_files = find_workflows(workflow_file=config.workflow_file)
        console.print(f"Validating specific workflow: {config.workflow_file}")
    elif config.changed_only:
        console.print("Identifying changed workflows...")
        workflow_files = find_workflows(changed_only=True)
        console.print(f"Found {len(workflow_files)} changed workflow files.")
    else:
        console.print("Identifying all workflows...")
        workflow_files = find_workflows()
        console.print(f"Found {len(workflow_files)} workflow files.")

    if not workflow_files:
        console.print("[yellow]No workflows to validate.[/yellow]")
        return

    # If dry run is specified, just list the workflows
    if config.dry_run:
        console.print("\n[bold]Dry run mode - would validate these workflows:[/bold]")
        for wf in workflow_files:
            console.print(f"  - {wf.name}")
        console.print("\n[green]Dry run completed successfully.[/green]")
        return

    # Validate workflow syntax
    console.print("\n[bold]Step 1: Validating workflow syntax with actionlint...[/bold]")
    if config.skip_lint:
        console.print("[yellow]Skipping actionlint validation (skip_lint flag is set)...[/yellow]")
    else:
        syntax_success, syntax_errors = validate_all_syntax(workflow_files, config)
        if not syntax_success:
            console.print("\n[bold red]❌ Syntax validation failed.[/bold red]")
            for error in syntax_errors:
                reporter.add_error(
                    SyntaxError(
                        message=error,
                        file=Path("unknown"),  # We don't have the file info here
                        suggestion="Check the workflow syntax using the GitHub Actions documentation.",
                    )
                )
            sys.exit(1)
        else:
            console.print("[bold green]✅ Syntax validation passed.[/bold green]")

    # Validate workflow execution
    console.print("\n[bold]Step 2: Running workflows in local containers with act...[/bold]")
    start_time = time.time()
    execution_success, execution_errors = validate_all_execution(workflow_files, config)
    elapsed_time = time.time() - start_time

    # Print summary
    if execution_success:
        console.print(
            f"\n[bold green]✅ All workflows validated successfully in {elapsed_time:.2f} seconds![/bold green]"
        )
    else:
        console.print(
            f"\n[bold red]❌ One or more workflows failed validation (elapsed time: {elapsed_time:.2f} seconds)[/bold red]"
        )
        for error in execution_errors:
            reporter.add_error(
                ExecutionError(
                    message=error,
                    file=Path("unknown"),  # We don't have the file info here
                    suggestion="Check the workflow execution using the GitHub Actions documentation.",
                )
            )
        sys.exit(1)


@cli.group()
def docs():
    """Documentation workflow commands."""
    pass


@docs.command()
@click.option("--port", default=8000, help="Port to run the server on")
def preview(port: int):
    """Run a local preview server for documentation.

    This command runs a local preview server for documentation using MkDocs.

    Examples:
        # Run a preview server on the default port (8000)
        validate-github-workflows docs preview

        # Run a preview server on a custom port
        validate-github-workflows docs preview --port 8080
    """
    try:
        import subprocess

        console.print(f"Starting documentation preview server on port {port}...")
        subprocess.run(["mkdocs", "serve", "--dev-addr", f"localhost:{port}"])
    except FileNotFoundError:
        console.print("[bold red]Error: mkdocs command not found.[/bold red]")
        console.print("Please install mkdocs:")
        console.print("  pip install mkdocs")
        sys.exit(1)


@docs.command()
def build():
    """Build documentation without serving.

    This command builds the documentation using MkDocs without starting a server.

    Examples:
        # Build documentation
        validate-github-workflows docs build
    """
    try:
        import subprocess

        console.print("Building documentation...")
        subprocess.run(["mkdocs", "build", "--strict"])
        console.print(
            "[bold green]Documentation built successfully to ./site directory[/bold green]"
        )
    except FileNotFoundError:
        console.print("[bold red]Error: mkdocs command not found.[/bold red]")
        console.print("Please install mkdocs:")
        console.print("  pip install mkdocs")
        sys.exit(1)


@cli.command()
@click.option("--output", default=".github-actions-validator.json", help="Output file path")
def init(output: str):
    """Initialize a configuration file with default values.

    This command creates a configuration file with default values that can be
    customized for your project.

    Examples:
        # Create a default configuration file
        validate-github-workflows init

        # Create a configuration file with a custom name
        validate-github-workflows init --output my-config.json
    """
    import json

    # Create default settings
    config = ValidationConfig.create()

    # Convert to dictionary
    config_dict = config.model_dump()

    # Write to file
    with open(output, "w") as f:
        json.dump(config_dict, f, indent=2)

    console.print(f"[bold green]Configuration file created at {output}[/bold green]")
    console.print("You can now customize this file for your project.")


def main():
    """Main entry point for the package."""
    cli()


if __name__ == "__main__":
    main()
