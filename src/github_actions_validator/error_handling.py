"""Error handling and reporting for GitHub Actions workflow validation."""

import logging
import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Protocol

# Get the logger
logger = logging.getLogger("github_actions_validator")

try:
    # Import rich components if available
    from rich.panel import Panel
    from rich.syntax import Syntax

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Console(Protocol):
    """Protocol for console objects that have a print method."""

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to the console."""
        ...


class ErrorSeverity(Enum):
    """Severity levels for validation errors."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class ValidationError:
    """Represents a validation error with context and suggestions.

    Attributes:
        message: The main error message
        severity: The severity level of the error
        workflow_file: The name of the workflow file where the error occurred
        job_name: The name of the job where the error occurred (if applicable)
        line_number: The line number where the error occurred (if applicable)
        context: Additional context about the error (e.g., surrounding code)
        suggestion: A suggestion for fixing the error
        error_type: Categorized error type (e.g., syntax, reference, permission)
        context_before: Lines of code before the error line
        context_after: Lines of code after the error line
        error_line: The exact line with the error
        raw_output: The raw output from the command that produced the error
    """

    message: str
    severity: ErrorSeverity
    workflow_file: str | Path | None = None
    job_name: str | None = None
    line_number: int | None = None
    context: str | None = None
    suggestion: str | None = None
    error_type: str | None = None
    context_before: list[str] | None = None
    context_after: list[str] | None = None
    error_line: str | None = None
    raw_output: str | None = None

    def __post_init__(self):
        """Convert Path objects to strings for workflow_file."""
        if isinstance(self.workflow_file, Path):
            self.workflow_file = str(self.workflow_file)


class ErrorReporter:
    """Handles error reporting and suggestions for workflow validation.

    This class provides methods for formatting and reporting errors with
    helpful suggestions for fixing common issues.

    Attributes:
        console: A Rich console for formatted output (if available)
        error_patterns: A dictionary mapping error patterns to suggestions
    """

    def __init__(self, console: Console | None = None):
        """Initialize the error reporter.

        Args:
            console: A Rich console for formatted output (optional)
        """
        self.console = console if console and RICH_AVAILABLE else None

        # Common error patterns and suggestions
        self.error_patterns = {
            r"No such file or directory": "Check if all referenced files exist in the repository",
            r"Unknown action": (
                "Make sure the action is publicly available or included in the repository"
            ),
            r"Invalid workflow file": "Validate the YAML syntax of your workflow file",
            r"not found": "Ensure the referenced resource exists and is accessible",
            r"permission denied": "Check file permissions or if you need elevated privileges",
            r"Could not find a version": (
                "The specified package version may not exist "
                "or be available in the current environment"
            ),
            r"Could not find any stages to run": (
                "This is likely due to event trigger mismatch. "
                "Check that your workflow triggers match the event type you're testing with."
            ),
            r"exit status \d+": (
                "The action failed with a non-zero exit code. "
                "Check the action's logs for more details."
            ),
            r"Unknown input '([^']+)'": (
                "The action doesn't accept the input '{0}'. "
                "Check the action's documentation for valid inputs."
            ),
            r"The workflow is not valid": (
                "The workflow file has syntax errors. Run 'actionlint' to identify specific issues."
            ),
            r"Docker (daemon|engine) is not running": (
                "Make sure Docker is installed and running before validating workflows."
            ),
            r"Error: ([^@]+)@([^ ]+) not found": (
                "The action '{0}@{1}' was not found. Check the name and version."
            ),
            r"Error: ([^@]+) not found": (
                "The action '{0}' was not found. "
                "Check the name and make sure it's publicly available."
            ),
        }

    def categorize_error(self, error_message: str) -> str:
        """Categorize error based on message content.

        Args:
            error_message: The error message to categorize

        Returns:
            The error category as a string
        """
        categories = {
            "syntax": [
                "invalid syntax",
                "parse error",
                "unexpected token",
                "invalid workflow file",
            ],
            "reference": ["not found", "undefined", "unknown action", "no such file"],
            "permission": ["permission denied", "access denied"],
            "timeout": ["timed out", "deadline exceeded"],
            "network": ["network error", "connection refused"],
            "docker": ["docker", "container", "image"],
            "event": ["could not find any stages to run", "event trigger"],
            "execution": ["exit status", "failed with exit code"],
        }

        for category, patterns in categories.items():
            if any(pattern in error_message.lower() for pattern in patterns):
                return category

        return "general"

    def _extract_context_lines(
        self, workflow_name: str | Path, line_number: int
    ) -> tuple[list[str] | None, str | None, list[str] | None]:
        """Extract context lines from a workflow file around a specific line number.

        Args:
            workflow_name: The name of the workflow file
            line_number: The line number to extract context around

        Returns:
            A tuple of (context_before, error_line, context_after)
        """
        context_before = None
        error_line = None
        context_after = None

        try:
            workflow_path = Path(workflow_name)
            if workflow_path.exists():
                with open(workflow_path) as f:
                    lines = f.readlines()

                    # Get context lines (3 lines before and after the error)
                    start_line = max(0, line_number - 4)
                    end_line = min(len(lines), line_number + 3)

                    if line_number - 1 < len(lines):
                        context_before = lines[start_line : line_number - 1]
                        error_line = lines[line_number - 1]
                        context_after = lines[line_number:end_line]
        except Exception as e:
            logger.debug(f"Error extracting context lines: {e}")

        return context_before, error_line, context_after

    def _match_error_pattern(self, error_message: str) -> tuple[str | None, ErrorSeverity]:
        """Match error message against known patterns and determine suggestion.

        Args:
            error_message: The error message to match

        Returns:
            A tuple of (suggestion, severity)
        """
        suggestion = None
        severity = ErrorSeverity.ERROR

        # Check for known error patterns and provide suggestions
        for pattern, hint in self.error_patterns.items():
            match = re.search(pattern, error_message)
            if match:
                # If the pattern has capture groups, format the suggestion with them
                if match.groups():
                    suggestion = hint.format(*match.groups())
                else:
                    suggestion = hint

                # Set severity to ERROR for "Unknown action" errors
                if pattern == r"Unknown action":
                    severity = ErrorSeverity.ERROR
                break

        return suggestion, severity

    def _determine_severity(
        self, error_message: str, initial_severity: ErrorSeverity
    ) -> ErrorSeverity:
        """Determine the severity of an error based on its message.

        Args:
            error_message: The error message
            initial_severity: The initial severity to use

        Returns:
            The determined severity level
        """
        if "warning" in error_message.lower():
            return ErrorSeverity.WARNING
        elif (
            "error" in error_message.lower()
            or "failed" in error_message.lower()
            or "unknown action" in error_message.lower()
        ):
            return ErrorSeverity.ERROR
        elif "critical" in error_message.lower():
            return ErrorSeverity.CRITICAL

        return initial_severity

    def format_error(
        self,
        error_message: str,
        workflow_name: str | Path | None = None,
        job_name: str | None = None,
        line_number: int | None = None,
        context: str | None = None,
        raw_output: str | None = None,
    ) -> ValidationError:
        """Format error message with helpful suggestions.

        Args:
            error_message: The error message to format
            workflow_name: The name of the workflow file (optional)
            job_name: The name of the job (optional)
            line_number: The line number where the error occurred (optional)
            context: Additional context about the error (optional)
            raw_output: The raw output from the command that produced the error (optional)

        Returns:
            A ValidationError object with formatted error information
        """
        error_type = self.categorize_error(error_message)
        context_before = None
        context_after = None
        error_line = None

        # Extract context lines if workflow file and line number are provided
        if workflow_name and line_number and isinstance(workflow_name, str | Path):
            context_before, error_line, context_after = self._extract_context_lines(
                workflow_name, line_number
            )

        # Match error pattern and get initial suggestion and severity
        suggestion, severity = self._match_error_pattern(error_message)

        # Determine final severity based on error message
        severity = self._determine_severity(error_message, severity)

        return ValidationError(
            message=error_message,
            severity=severity,
            workflow_file=workflow_name,
            job_name=job_name,
            line_number=line_number,
            context=context,
            suggestion=suggestion,
            error_type=error_type,
            context_before=context_before,
            context_after=context_after,
            error_line=error_line,
            raw_output=raw_output,
        )

    def _get_error_title(self, error: ValidationError) -> str:
        """Build an error title from the error information.

        Args:
            error: The ValidationError to build a title for

        Returns:
            A formatted error title
        """
        title = f"Error in {error.workflow_file}" if error.workflow_file else "Error"
        if error.job_name:
            title += f" (job: {error.job_name})"
        if error.line_number:
            title += f" (line: {error.line_number})"
        if error.error_type:
            title += f" (type: {error.error_type})"
        return title

    def _format_context_lines_rich(self, error: ValidationError) -> list[str]:
        """Format context lines for rich output.

        Args:
            error: The ValidationError containing context lines

        Returns:
            A list of formatted context lines
        """
        context_lines = []

        # Add context before
        if error.context_before and error.line_number is not None:
            line_num = int(error.line_number)  # Ensure it's an integer
            line_num_start = line_num - len(error.context_before)
            for i, line in enumerate(error.context_before):
                context_lines.append(f"{line_num_start + i} | {line.rstrip()}")

        # Add error line (highlighted)
        if error.line_number is not None and error.error_line:
            line_num = int(error.line_number)  # Ensure it's an integer
            context_lines.append(f"[bold red]{line_num} | {error.error_line.rstrip()}[/bold red]")

        # Add context after
        if error.context_after and error.line_number is not None:
            line_num = int(error.line_number)  # Ensure it's an integer
            for i, line in enumerate(error.context_after):
                context_lines.append(f"{line_num + i + 1} | {line.rstrip()}")

        return context_lines

    def _report_with_rich(self, error: ValidationError, title: str, color: str) -> None:
        """Report an error using rich formatting.

        Args:
            error: The ValidationError to report
            title: The error title
            color: The color to use for the error
        """
        # Print the main message in a panel
        if self.console:
            self.console.print(Panel(error.message, title=title, border_style=color))
        else:
            print(f"{title}: {error.message}")

        # If there's an error line with context, print it as syntax-highlighted code
        if error.error_line:
            if self.console:
                self.console.print("Error location:")
                context_lines = self._format_context_lines_rich(error)
                self.console.print("\n".join(context_lines))
            else:
                print("Error location:")
        # If there's just general context, print it
        elif error.context:
            if self.console:
                self.console.print("Context:")
                syntax = Syntax(error.context, "yaml", theme="monokai", line_numbers=True)
                self.console.print(syntax)
            else:
                print("Context:")
                print(error.context)

        # If there's a suggestion, print it
        if error.suggestion:
            if self.console:
                self.console.print(f"[bold]Suggestion:[/bold] {error.suggestion}")
            else:
                print(f"Suggestion: {error.suggestion}")

    def _report_with_plain_text(self, error: ValidationError, title: str) -> None:
        """Report an error using plain text.

        Args:
            error: The ValidationError to report
            title: The error title
        """
        print(f"\n{title}")
        print("=" * len(title))
        print(error.message)

        # Print error line with context
        if error.error_line:
            print("\nError location:")

            # Add context before
            if error.context_before and error.line_number is not None:
                line_num = int(error.line_number)  # Ensure it's an integer
                line_num_start = line_num - len(error.context_before)
                for i, line in enumerate(error.context_before):
                    print(f"{line_num_start + i} | {line.rstrip()}")

            # Add error line
            if error.line_number is not None and error.error_line:
                line_num = int(error.line_number)  # Ensure it's an integer
                print(f"{line_num} | {error.error_line.rstrip()} <-- ERROR")

            # Add context after
            if error.context_after and error.line_number is not None:
                line_num = int(error.line_number)  # Ensure it's an integer
                for i, line in enumerate(error.context_after):
                    print(f"{line_num + i + 1} | {line.rstrip()}")
        # If there's just general context, print it
        elif error.context:
            print("\nContext:")
            print(error.context)

        if error.suggestion:
            print(f"\nSuggestion: {error.suggestion}")

        print()

    def report_error(self, error: ValidationError) -> None:
        """Report an error with rich formatting if available.

        Args:
            error: The ValidationError to report
        """
        # Determine color based on severity
        color_map = {
            ErrorSeverity.INFO: "blue",
            ErrorSeverity.WARNING: "yellow",
            ErrorSeverity.ERROR: "red",
            ErrorSeverity.CRITICAL: "red bold",
        }
        color = color_map.get(error.severity, "white")

        # Build error message title
        title = self._get_error_title(error)

        # Use rich formatting if available, otherwise use plain text
        if self.console and RICH_AVAILABLE:
            self._report_with_rich(error, title, color)
        else:
            self._report_with_plain_text(error, title)

    def report_errors(self, errors: list[ValidationError]) -> None:
        """Report multiple errors.

        Args:
            errors: A list of ValidationError objects to report
        """
        for error in errors:
            self.report_error(error)

    def _extract_line_number(self, output: str, patterns: list[str]) -> int | None:
        """Extract line number from output using a list of patterns.

        Args:
            output: The output to extract line number from
            patterns: A list of regex patterns to try

        Returns:
            The extracted line number, or None if not found
        """
        for pattern in patterns:
            line_match = re.search(pattern, output)
            if line_match:
                try:
                    return int(line_match.group(1))
                except ValueError:
                    pass
        return None

    def _detect_unknown_action(
        self,
        output: str,
        workflow_file: str | Path | None,
        job_name: str | None,
        line_number_patterns: list[str],
    ) -> list[ValidationError]:
        """Detect unknown action errors in the output.

        Args:
            output: The output to analyze
            workflow_file: The workflow file being validated
            job_name: The job being validated
            line_number_patterns: Patterns to extract line numbers

        Returns:
            A list of ValidationError objects for unknown action errors
        """
        errors = []
        if "Unknown action" in output:
            # Extract the action name
            match = re.search(r"Unknown action: '([^']+)'", output)
            if match:
                action_name = match.group(1)
                line_number = self._extract_line_number(output, line_number_patterns)

                errors.append(
                    ValidationError(
                        message=f"Unknown action: '{action_name}'",
                        severity=ErrorSeverity.ERROR,
                        workflow_file=workflow_file,
                        job_name=job_name,
                        line_number=line_number,
                        context=output,
                        suggestion="Check that the action name is correct and publicly available.",
                        error_type="reference",
                        raw_output=output,
                    )
                )
        return errors

    def _detect_missing_stages(
        self, output: str, workflow_file: str | Path | None, job_name: str | None
    ) -> list[ValidationError]:
        """Detect missing stages errors in the output.

        Args:
            output: The output to analyze
            workflow_file: The workflow file being validated
            job_name: The job being validated

        Returns:
            A list of ValidationError objects for missing stages errors
        """
        errors = []
        if "Could not find any stages to run" in output:
            errors.append(
                ValidationError(
                    message="Could not find any stages to run",
                    severity=ErrorSeverity.WARNING,
                    workflow_file=workflow_file,
                    job_name=job_name,
                    context=output,
                    suggestion=(
                        "This is likely due to event trigger mismatch. "
                        "Check that your workflow triggers match the event type "
                        "you're testing with."
                    ),
                    error_type="event",
                    raw_output=output,
                )
            )
        return errors

    def _detect_docker_issues(
        self, output: str, workflow_file: str | Path | None, job_name: str | None
    ) -> list[ValidationError]:
        """Detect Docker-related issues in the output.

        Args:
            output: The output to analyze
            workflow_file: The workflow file being validated
            job_name: The job being validated

        Returns:
            A list of ValidationError objects for Docker-related issues
        """
        errors = []
        if (
            "Cannot connect to the Docker daemon" in output
            or "docker daemon is not running" in output
        ):
            errors.append(
                ValidationError(
                    message="Docker daemon is not running",
                    severity=ErrorSeverity.ERROR,
                    workflow_file=workflow_file,
                    job_name=job_name,
                    context=output,
                    suggestion=(
                        "Make sure Docker is installed and running before validating workflows."
                    ),
                    error_type="docker",
                    raw_output=output,
                )
            )
        return errors

    def _detect_exit_status(
        self, output: str, workflow_file: str | Path | None, job_name: str | None
    ) -> list[ValidationError]:
        """Detect exit status errors in the output.

        Args:
            output: The output to analyze
            workflow_file: The workflow file being validated
            job_name: The job being validated

        Returns:
            A list of ValidationError objects for exit status errors
        """
        errors = []
        exit_status_match = re.search(r"exit status (\d+)", output)
        if exit_status_match:
            exit_code = exit_status_match.group(1)

            # Try to extract more context about the error
            error_context = output
            # Look for the last few lines before the exit status message
            lines = output.splitlines()
            for i, line in enumerate(lines):
                if "exit status" in line and i > 5:
                    error_context = "\n".join(lines[i - 5 : i + 1])
                    break

            errors.append(
                ValidationError(
                    message=f"Process exited with status {exit_code}",
                    severity=ErrorSeverity.ERROR,
                    workflow_file=workflow_file,
                    job_name=job_name,
                    context=error_context,
                    suggestion="Check the error message for details on what went wrong.",
                    error_type="execution",
                    raw_output=output,
                )
            )
        return errors

    def _detect_syntax_errors(
        self,
        output: str,
        workflow_file: str | Path | None,
        job_name: str | None,
        line_number_patterns: list[str],
    ) -> list[ValidationError]:
        """Detect syntax errors in the output.

        Args:
            output: The output to analyze
            workflow_file: The workflow file being validated
            job_name: The job being validated
            line_number_patterns: Patterns to extract line numbers

        Returns:
            A list of ValidationError objects for syntax errors
        """
        errors = []
        syntax_error_match = re.search(
            r"(syntax error|parse error|invalid syntax|invalid workflow file)", output.lower()
        )
        if syntax_error_match:
            line_number = self._extract_line_number(output, line_number_patterns)

            errors.append(
                ValidationError(
                    message="Syntax error in workflow file",
                    severity=ErrorSeverity.ERROR,
                    workflow_file=workflow_file,
                    job_name=job_name,
                    line_number=line_number,
                    context=output,
                    suggestion=(
                        "Check the syntax of your workflow file. "
                        "Use actionlint for detailed syntax validation."
                    ),
                    error_type="syntax",
                    raw_output=output,
                )
            )
        return errors

    def analyze_act_output(
        self, output: str, workflow_file: str | Path | None = None, job_name: str | None = None
    ) -> list[ValidationError]:
        """Analyze act output for errors and warnings.

        Args:
            output: The output from running act
            workflow_file: The workflow file being validated (optional)
            job_name: The job being validated (optional)

        Returns:
            A list of ValidationError objects extracted from the output
        """
        errors = []

        # Extract line numbers from error messages
        line_number_patterns = [
            r"line (\d+):",  # Common format: "line 42:"
            r"at line (\d+)",  # Another format: "at line 42"
            r":(\d+):",  # File:line:column format: "file.yml:42:10:"
        ]

        # Detect different types of errors
        errors.extend(
            self._detect_unknown_action(output, workflow_file, job_name, line_number_patterns)
        )
        errors.extend(self._detect_missing_stages(output, workflow_file, job_name))
        errors.extend(self._detect_docker_issues(output, workflow_file, job_name))
        errors.extend(self._detect_exit_status(output, workflow_file, job_name))
        errors.extend(
            self._detect_syntax_errors(output, workflow_file, job_name, line_number_patterns)
        )

        # If no specific errors were found but the output contains "error", create a generic error
        if not errors and "error" in output.lower():
            line_number = self._extract_line_number(output, line_number_patterns)

            errors.append(
                self.format_error(
                    error_message="An error occurred during workflow validation",
                    workflow_name=workflow_file,
                    job_name=job_name,
                    line_number=line_number,
                    context=output,
                    raw_output=output,
                )
            )

        return errors
