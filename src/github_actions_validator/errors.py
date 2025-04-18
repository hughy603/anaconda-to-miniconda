"""Error handling for GitHub Actions validation.

This module provides error handling and reporting for GitHub Actions validation.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel


class ValidationError(Exception):
    """Base class for validation errors."""

    def __init__(
        self,
        message: str,
        file: Path,
        suggestion: str | None = None,
        context: str | None = None,
    ):
        """Initialize a validation error.

        Args:
            message: The error message
            file: The file where the error occurred
            suggestion: A suggestion for fixing the error (optional)
            context: Context information about the error (optional)
        """
        self.message = message
        self.file = file
        self.suggestion = suggestion
        self.context = context
        super().__init__(message)


class SyntaxError(ValidationError):
    """Error for syntax validation failures."""

    pass


class ExecutionError(ValidationError):
    """Error for execution validation failures."""

    pass


class ErrorReporter:
    """Reporter for validation errors."""

    def __init__(self, verbose: bool = False):
        """Initialize an error reporter.

        Args:
            verbose: Whether to show verbose output
        """
        self.verbose = verbose
        self.console = Console()
        self.errors: list[ValidationError] = []

    def add_error(self, error: ValidationError) -> None:
        """Add an error to the reporter.

        Args:
            error: The validation error
        """
        self.errors.append(error)
        self.display_error(error)

    def display_error(self, error: ValidationError) -> None:
        """Display a validation error.

        Args:
            error: The validation error
        """
        # Determine color based on error type
        if isinstance(error, SyntaxError):
            color = "yellow"
            title = "Syntax Error"
        elif isinstance(error, ExecutionError):
            color = "red"
            title = "Execution Error"
        else:
            color = "magenta"
            title = "Validation Error"

        # Display error
        self.console.print(
            Panel(
                f"[bold]{error.message}[/bold]\n\n"
                f"File: [cyan]{error.file}[/cyan]"
                + (f"\n\nContext: [blue]{error.context}[/blue]" if error.context else "")
                + (
                    f"\n\nSuggestion: [green]{error.suggestion}[/green]" if error.suggestion else ""
                ),
                title=title,
                border_style=color,
            )
        )

    def has_errors(self) -> bool:
        """Check if there are any errors.

        Returns:
            True if there are errors, False otherwise
        """
        return len(self.errors) > 0

    def get_error_count(self) -> int:
        """Get the number of errors.

        Returns:
            The number of errors
        """
        return len(self.errors)

    def summarize(self) -> None:
        """Summarize all errors."""
        if not self.errors:
            self.console.print("[bold green]No validation errors found![/bold green]")
            return

        syntax_errors = sum(1 for e in self.errors if isinstance(e, SyntaxError))
        execution_errors = sum(1 for e in self.errors if isinstance(e, ExecutionError))
        other_errors = len(self.errors) - syntax_errors - execution_errors

        self.console.print(
            f"[bold red]Found {len(self.errors)} validation errors:[/bold red]\n"
            f"  - {syntax_errors} syntax errors\n"
            f"  - {execution_errors} execution errors\n"
            f"  - {other_errors} other errors"
        )
