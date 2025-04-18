"""Tests for the errors module."""

from pathlib import Path
from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel

from github_actions_validator.errors import (
    ErrorReporter,
    ExecutionError,
    SyntaxError,
    ValidationError,
)


class TestValidationError:
    """Tests for the ValidationError class."""

    def test_init(self):
        """Test initialization of ValidationError."""
        file = Path(".github/workflows/ci.yml")
        error = ValidationError(
            message="Test error",
            file=file,
            suggestion="Fix the error",
            context="Error context",
        )

        assert error.message == "Test error"
        assert error.file == file
        assert error.suggestion == "Fix the error"
        assert error.context == "Error context"

    def test_init_minimal(self):
        """Test initialization with minimal parameters."""
        file = Path(".github/workflows/ci.yml")
        error = ValidationError(message="Test error", file=file)

        assert error.message == "Test error"
        assert error.file == file
        assert error.suggestion is None
        assert error.context is None


class TestSyntaxError:
    """Tests for the SyntaxError class."""

    def test_init(self):
        """Test initialization of SyntaxError."""
        file = Path(".github/workflows/ci.yml")
        error = SyntaxError(
            message="Syntax error",
            file=file,
            suggestion="Fix the syntax",
            context="Syntax context",
        )

        assert error.message == "Syntax error"
        assert error.file == file
        assert error.suggestion == "Fix the syntax"
        assert error.context == "Syntax context"
        assert isinstance(error, ValidationError)


class TestExecutionError:
    """Tests for the ExecutionError class."""

    def test_init(self):
        """Test initialization of ExecutionError."""
        file = Path(".github/workflows/ci.yml")
        error = ExecutionError(
            message="Execution error",
            file=file,
            suggestion="Fix the execution",
            context="Execution context",
        )

        assert error.message == "Execution error"
        assert error.file == file
        assert error.suggestion == "Fix the execution"
        assert error.context == "Execution context"
        assert isinstance(error, ValidationError)


class TestErrorReporter:
    """Tests for the ErrorReporter class."""

    def test_init(self):
        """Test initialization of ErrorReporter."""
        reporter = ErrorReporter()
        assert reporter.verbose is False
        assert isinstance(reporter.console, Console)
        assert reporter.errors == []

        reporter = ErrorReporter(verbose=True)
        assert reporter.verbose is True

    def test_add_error(self):
        """Test adding an error to the reporter."""
        reporter = ErrorReporter()
        file = Path(".github/workflows/ci.yml")
        error = ValidationError(message="Test error", file=file)

        with patch.object(reporter, "display_error") as mock_display:
            reporter.add_error(error)
            assert len(reporter.errors) == 1
            assert reporter.errors[0] == error
            mock_display.assert_called_once_with(error)

    @patch("rich.console.Console.print")
    def test_display_error_syntax(self, mock_print):
        """Test displaying a syntax error."""
        reporter = ErrorReporter()
        file = Path(".github/workflows/ci.yml")
        error = SyntaxError(
            message="Syntax error",
            file=file,
            suggestion="Fix the syntax",
            context="Syntax context",
        )

        reporter.display_error(error)
        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        panel = args[0]
        assert isinstance(panel, Panel)
        assert "Syntax error" in panel.renderable
        assert "Fix the syntax" in panel.renderable
        assert "Syntax context" in panel.renderable
        assert panel.title == "Syntax Error"
        assert panel.border_style == "yellow"

    @patch("rich.console.Console.print")
    def test_display_error_execution(self, mock_print):
        """Test displaying an execution error."""
        reporter = ErrorReporter()
        file = Path(".github/workflows/ci.yml")
        error = ExecutionError(
            message="Execution error",
            file=file,
            suggestion="Fix the execution",
            context="Execution context",
        )

        reporter.display_error(error)
        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        panel = args[0]
        assert isinstance(panel, Panel)
        assert "Execution error" in panel.renderable
        assert "Fix the execution" in panel.renderable
        assert "Execution context" in panel.renderable
        assert panel.title == "Execution Error"
        assert panel.border_style == "red"

    @patch("rich.console.Console.print")
    def test_display_error_validation(self, mock_print):
        """Test displaying a generic validation error."""
        reporter = ErrorReporter()
        file = Path(".github/workflows/ci.yml")
        error = ValidationError(
            message="Validation error",
            file=file,
            suggestion="Fix the validation",
            context="Validation context",
        )

        reporter.display_error(error)
        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        panel = args[0]
        assert isinstance(panel, Panel)
        assert "Validation error" in panel.renderable
        assert "Fix the validation" in panel.renderable
        assert "Validation context" in panel.renderable
        assert panel.title == "Validation Error"
        assert panel.border_style == "magenta"

    @patch("rich.console.Console.print")
    def test_display_error_without_context_suggestion(self, mock_print):
        """Test displaying an error without context or suggestion."""
        reporter = ErrorReporter()
        file = Path(".github/workflows/ci.yml")
        error = ValidationError(message="Validation error", file=file)

        reporter.display_error(error)
        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        panel = args[0]
        assert isinstance(panel, Panel)
        assert "Validation error" in panel.renderable
        assert "Context" not in panel.renderable
        assert "Suggestion" not in panel.renderable

    def test_has_errors(self):
        """Test checking if there are errors."""
        reporter = ErrorReporter()
        assert reporter.has_errors() is False

        file = Path(".github/workflows/ci.yml")
        error = ValidationError(message="Test error", file=file)
        reporter.errors.append(error)
        assert reporter.has_errors() is True

    def test_get_error_count(self):
        """Test getting the error count."""
        reporter = ErrorReporter()
        assert reporter.get_error_count() == 0

        file = Path(".github/workflows/ci.yml")
        error1 = ValidationError(message="Test error 1", file=file)
        error2 = ValidationError(message="Test error 2", file=file)
        reporter.errors.extend([error1, error2])
        assert reporter.get_error_count() == 2

    @patch("rich.console.Console.print")
    def test_summarize_no_errors(self, mock_print):
        """Test summarizing with no errors."""
        reporter = ErrorReporter()
        reporter.summarize()
        mock_print.assert_called_once_with("[bold green]No validation errors found![/bold green]")

    @patch("rich.console.Console.print")
    def test_summarize_with_errors(self, mock_print):
        """Test summarizing with errors."""
        reporter = ErrorReporter()
        file = Path(".github/workflows/ci.yml")

        syntax_error = SyntaxError(message="Syntax error", file=file)
        execution_error = ExecutionError(message="Execution error", file=file)
        validation_error = ValidationError(message="Validation error", file=file)

        reporter.errors.extend([syntax_error, execution_error, validation_error])
        reporter.summarize()

        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        summary = args[0]

        assert "Found 3 validation errors" in summary
        assert "1 syntax errors" in summary
        assert "1 execution errors" in summary
        assert "1 other errors" in summary
