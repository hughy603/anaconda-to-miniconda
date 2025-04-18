"""Extended tests for the error handling module to increase coverage."""

from pathlib import Path
from unittest.mock import mock_open, patch

from github_actions_validator.error_handling import ErrorReporter, ErrorSeverity, ValidationError


class TestErrorHandlingExtended:
    """Extended tests for the error handling module."""

    def test_validation_error_with_all_fields(self):
        """Test ValidationError class with all fields."""
        error = ValidationError(
            message="Test error",
            severity=ErrorSeverity.ERROR,
            workflow_file="ci.yml",
            job_name="build",
            line_number=10,
            context="context",
            suggestion="suggestion",
            error_type="syntax",
            context_before=["line 8", "line 9"],
            context_after=["line 11", "line 12"],
            error_line="line 10 with error",
            raw_output="raw output",
        )
        assert error.message == "Test error"
        assert error.severity == ErrorSeverity.ERROR
        assert error.workflow_file == "ci.yml"
        assert error.job_name == "build"
        assert error.line_number == 10
        assert error.context == "context"
        assert error.suggestion == "suggestion"
        assert error.error_type == "syntax"
        assert error.context_before == ["line 8", "line 9"]
        assert error.context_after == ["line 11", "line 12"]
        assert error.error_line == "line 10 with error"
        assert error.raw_output == "raw output"

    def test_validation_error_with_path_object(self):
        """Test ValidationError with Path object for workflow_file."""
        workflow_file = Path(".github/workflows/ci.yml")
        error = ValidationError(
            message="Test error",
            severity=ErrorSeverity.ERROR,
            workflow_file=workflow_file,
        )
        assert error.workflow_file == str(workflow_file)

    def test_error_severity_values(self):
        """Test all ErrorSeverity enum values."""
        assert ErrorSeverity.INFO.name == "INFO"
        assert ErrorSeverity.WARNING.name == "WARNING"
        assert ErrorSeverity.ERROR.name == "ERROR"
        assert ErrorSeverity.CRITICAL.name == "CRITICAL"

        # Test ordering
        assert ErrorSeverity.INFO.value < ErrorSeverity.WARNING.value
        assert ErrorSeverity.WARNING.value < ErrorSeverity.ERROR.value
        assert ErrorSeverity.ERROR.value < ErrorSeverity.CRITICAL.value

    def test_error_reporter_categorize_error_all_categories(self):
        """Test ErrorReporter.categorize_error method with all categories."""
        reporter = ErrorReporter()

        # Test all categories
        assert reporter.categorize_error("invalid syntax") == "syntax"
        assert reporter.categorize_error("parse error") == "syntax"
        assert reporter.categorize_error("unexpected token") == "syntax"
        assert reporter.categorize_error("invalid workflow file") == "syntax"

        assert reporter.categorize_error("not found") == "reference"
        assert reporter.categorize_error("undefined") == "reference"
        assert reporter.categorize_error("unknown action") == "reference"
        assert reporter.categorize_error("no such file") == "reference"

        assert reporter.categorize_error("permission denied") == "permission"
        assert reporter.categorize_error("access denied") == "permission"

        assert reporter.categorize_error("timed out") == "timeout"
        assert reporter.categorize_error("deadline exceeded") == "timeout"

        assert reporter.categorize_error("network error") == "network"
        assert reporter.categorize_error("connection refused") == "network"

        assert reporter.categorize_error("docker") == "docker"
        assert reporter.categorize_error("container") == "docker"
        assert reporter.categorize_error("image") == "docker"

        assert reporter.categorize_error("could not find any stages to run") == "event"
        assert reporter.categorize_error("event trigger") == "event"

        assert reporter.categorize_error("exit status") == "execution"
        assert reporter.categorize_error("failed with exit code") == "execution"

        assert reporter.categorize_error("unknown error type") == "general"

    @patch("builtins.open", new_callable=mock_open, read_data="line1\nline2\nline3\nline4\nline5\n")
    @patch("pathlib.Path.exists")
    def test_extract_context_lines(self, mock_exists, mock_file):
        """Test _extract_context_lines method."""
        mock_exists.return_value = True

        reporter = ErrorReporter()
        workflow_file = Path(".github/workflows/ci.yml")

        # Test with line in the middle
        context_before, error_line, context_after = reporter._extract_context_lines(
            workflow_file, 3
        )
        assert context_before == ["line1\n", "line2\n"]
        assert error_line == "line3\n"
        assert context_after == ["line4\n", "line5\n"]

        # Test with first line
        context_before, error_line, context_after = reporter._extract_context_lines(
            workflow_file, 1
        )
        assert context_before == []
        assert error_line == "line1\n"
        assert context_after == ["line2\n", "line3\n", "line4\n"]

        # Test with last line
        context_before, error_line, context_after = reporter._extract_context_lines(
            workflow_file, 5
        )
        assert context_before == ["line2\n", "line3\n", "line4\n"]
        assert error_line == "line5\n"
        assert context_after == []

        # Test with line out of range
        context_before, error_line, context_after = reporter._extract_context_lines(
            workflow_file, 10
        )
        assert context_before is None
        assert error_line is None
        assert context_after is None

    @patch("pathlib.Path.exists")
    def test_extract_context_lines_file_not_found(self, mock_exists):
        """Test _extract_context_lines method with file not found."""
        mock_exists.return_value = False

        reporter = ErrorReporter()
        workflow_file = Path(".github/workflows/ci.yml")

        context_before, error_line, context_after = reporter._extract_context_lines(
            workflow_file, 3
        )
        assert context_before is None
        assert error_line is None
        assert context_after is None

    @patch("builtins.open", side_effect=Exception("Test exception"))
    @patch("pathlib.Path.exists")
    def test_extract_context_lines_exception(self, mock_exists, mock_file):
        """Test _extract_context_lines method with exception."""
        mock_exists.return_value = True

        reporter = ErrorReporter()
        workflow_file = Path(".github/workflows/ci.yml")

        context_before, error_line, context_after = reporter._extract_context_lines(
            workflow_file, 3
        )
        assert context_before is None
        assert error_line is None
        assert context_after is None

    def test_match_error_pattern(self):
        """Test _match_error_pattern method."""
        reporter = ErrorReporter()

        # Test with known error patterns
        suggestion, severity = reporter._match_error_pattern("No such file or directory")
        assert suggestion == "Check if all referenced files exist in the repository"
        assert severity == ErrorSeverity.ERROR

        suggestion, severity = reporter._match_error_pattern(
            "Unknown action: 'actions/setup-python@v4'"
        )
        assert (
            suggestion == "Make sure the action is publicly available or included in the repository"
        )
        assert severity == ErrorSeverity.ERROR

        suggestion, severity = reporter._match_error_pattern("Invalid workflow file")
        assert suggestion == "Validate the YAML syntax of your workflow file"
        assert severity == ErrorSeverity.ERROR

        # Test with unknown error pattern
        suggestion, severity = reporter._match_error_pattern("Unknown error message")
        assert suggestion is None
        assert severity == ErrorSeverity.ERROR

    def test_determine_severity(self):
        """Test _determine_severity method."""
        reporter = ErrorReporter()

        # Test with different error messages
        assert (
            reporter._determine_severity("warning: something", ErrorSeverity.INFO)
            == ErrorSeverity.WARNING
        )
        assert (
            reporter._determine_severity("error: something", ErrorSeverity.INFO)
            == ErrorSeverity.ERROR
        )
        assert (
            reporter._determine_severity("failed: something", ErrorSeverity.INFO)
            == ErrorSeverity.ERROR
        )
        assert (
            reporter._determine_severity("unknown action: something", ErrorSeverity.INFO)
            == ErrorSeverity.ERROR
        )
        assert (
            reporter._determine_severity("critical: something", ErrorSeverity.INFO)
            == ErrorSeverity.CRITICAL
        )

        # Test with initial severity
        assert (
            reporter._determine_severity("normal message", ErrorSeverity.INFO) == ErrorSeverity.INFO
        )
        assert (
            reporter._determine_severity("normal message", ErrorSeverity.WARNING)
            == ErrorSeverity.WARNING
        )
        assert (
            reporter._determine_severity("normal message", ErrorSeverity.ERROR)
            == ErrorSeverity.ERROR
        )
        assert (
            reporter._determine_severity("normal message", ErrorSeverity.CRITICAL)
            == ErrorSeverity.CRITICAL
        )

    def test_get_error_title(self):
        """Test _get_error_title method."""
        reporter = ErrorReporter()

        # Test with all fields
        error = ValidationError(
            message="Test error",
            severity=ErrorSeverity.ERROR,
            workflow_file="ci.yml",
            job_name="build",
            line_number=10,
            error_type="syntax",
        )
        title = reporter._get_error_title(error)
        assert title == "Error in ci.yml (job: build) (line: 10) (type: syntax)"

        # Test with minimal fields
        error = ValidationError(
            message="Test error",
            severity=ErrorSeverity.ERROR,
        )
        title = reporter._get_error_title(error)
        assert title == "Error"

        # Test with some fields
        error = ValidationError(
            message="Test error",
            severity=ErrorSeverity.ERROR,
            workflow_file="ci.yml",
        )
        title = reporter._get_error_title(error)
        assert title == "Error in ci.yml"
