"""Tests to improve code coverage for the GitHub Actions validator package."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from github_actions_validator.config import ValidationConfig
from github_actions_validator.error_handling import ErrorReporter, ErrorSeverity, ValidationError
from github_actions_validator.runners.act import ActRunner
from github_actions_validator.validators.syntax import check_actionlint_installed, validate_syntax


class TestErrorHandling:
    """Tests for the error handling module."""

    def test_error_severity(self):
        """Test ErrorSeverity enum."""
        assert ErrorSeverity.INFO.name == "INFO"
        assert ErrorSeverity.WARNING.name == "WARNING"
        assert ErrorSeverity.ERROR.name == "ERROR"
        assert ErrorSeverity.CRITICAL.name == "CRITICAL"

    def test_validation_error(self):
        """Test ValidationError class."""
        error = ValidationError(
            message="Test error", severity=ErrorSeverity.ERROR, workflow_file="ci.yml"
        )
        assert error.message == "Test error"
        assert error.severity == ErrorSeverity.ERROR
        assert error.workflow_file == "ci.yml"

    def test_error_reporter_init(self):
        """Test ErrorReporter initialization."""
        reporter = ErrorReporter()
        assert reporter.console is None

    def test_error_reporter_categorize_error(self):
        """Test ErrorReporter.categorize_error method."""
        reporter = ErrorReporter()
        assert reporter.categorize_error("invalid syntax") == "syntax"
        assert reporter.categorize_error("not found") == "reference"
        assert reporter.categorize_error("permission denied") == "permission"
        assert reporter.categorize_error("unknown error") == "general"


class TestValidatorsSyntax:
    """Tests for the syntax validator module."""

    @patch("subprocess.run")
    def test_validate_syntax_success(self, mock_run):
        """Test successful syntax validation."""
        # Mock subprocess.run to return success
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        error_reporter = ErrorReporter()
        workflow_file = Path(".github/workflows/ci.yml")

        success, errors = validate_syntax(workflow_file, error_reporter)

        assert success is True
        assert len(errors) == 0
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_validate_syntax_failure(self, mock_run):
        """Test failed syntax validation."""
        # Mock subprocess.run to return failure
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = "Error: Invalid workflow file"
        mock_process.stderr = ".github/workflows/ci.yml:10: error: Invalid syntax"
        mock_run.return_value = mock_process

        error_reporter = ErrorReporter()
        workflow_file = Path(".github/workflows/ci.yml")

        success, errors = validate_syntax(workflow_file, error_reporter)

        assert success is False
        assert len(errors) > 0
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_validate_syntax_file_not_found(self, mock_run):
        """Test syntax validation with file not found."""
        # Mock subprocess.run to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("No such file or directory")

        error_reporter = ErrorReporter()
        workflow_file = Path(".github/workflows/ci.yml")

        success, errors = validate_syntax(workflow_file, error_reporter)

        assert success is False
        assert len(errors) == 1
        assert errors[0].severity == ErrorSeverity.ERROR

    @patch("subprocess.run")
    def test_validate_syntax_exception(self, mock_run):
        """Test syntax validation with exception."""
        # Mock subprocess.run to raise an exception
        mock_run.side_effect = Exception("Test exception")

        error_reporter = ErrorReporter()
        workflow_file = Path(".github/workflows/ci.yml")

        success, errors = validate_syntax(workflow_file, error_reporter)

        assert success is False
        assert len(errors) == 1
        assert errors[0].severity == ErrorSeverity.ERROR

    @patch("subprocess.run")
    def test_check_actionlint_installed(self, mock_run):
        """Test checking if actionlint is installed."""
        # Mock subprocess.run to return success
        mock_process = MagicMock()
        mock_process.stdout = "actionlint help"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        result = check_actionlint_installed()

        assert result is True
        mock_run.assert_called_once()

        # Test with actionlint not installed
        mock_run.reset_mock()
        mock_process.stdout = ""
        mock_process.stderr = ""

        result = check_actionlint_installed()

        assert result is False

        # Test with FileNotFoundError
        mock_run.side_effect = FileNotFoundError("No such file or directory")

        result = check_actionlint_installed()

        assert result is False

        # Test with exception
        mock_run.side_effect = Exception("Test exception")

        result = check_actionlint_installed()

        assert result is False


class TestRunnersAct:
    """Tests for the act runner module."""

    def test_init(self):
        """Test initializing the ActRunner."""
        config = ValidationConfig.create()
        runner = ActRunner(config)

        assert runner.config == config

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_prepare_event_file(self, mock_json_dump, mock_file, mock_exists, mock_mkdir):
        """Test preparing event file."""
        # Mock Path.exists to return False
        mock_exists.return_value = False

        config = ValidationConfig.create()
        runner = ActRunner(config)

        # Test with push event
        event_file = runner.prepare_event_file("push")

        assert event_file == Path(".github/events/push.json")
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

        # Test with pull_request event
        mock_json_dump.reset_mock()

        event_file = runner.prepare_event_file("pull_request")

        assert event_file == Path(".github/events/pull_request.json")
        mock_json_dump.assert_called_once()

        # Test with schedule event
        mock_json_dump.reset_mock()

        event_file = runner.prepare_event_file("schedule")

        assert event_file == Path(".github/events/schedule.json")
        mock_json_dump.assert_called_once()

        # Test with existing event file
        mock_exists.return_value = True
        mock_json_dump.reset_mock()

        event_file = runner.prepare_event_file("push")

        assert event_file == Path(".github/events/push.json")
        mock_json_dump.assert_not_called()

    @patch("os.path.exists")
    def test_build_act_command(self, mock_exists):
        """Test building act command."""
        # Mock os.path.exists to return True
        mock_exists.return_value = True

        config = ValidationConfig.create()
        runner = ActRunner(config)

        # Test with default parameters
        with patch.object(
            runner, "prepare_event_file", return_value=Path(".github/events/push.json")
        ):
            cmd = runner.build_act_command(Path(".github/workflows/ci.yml"))

            assert cmd[0] == "act"
            assert "-W" in cmd
            assert ".github/workflows/ci.yml" in cmd
            assert "-e" in cmd
            assert ".github/events/push.json" in cmd
            assert "--action-cache-path" in cmd
            assert "--env" in cmd
            assert "-s" in cmd

        # Test with job filter
        with patch.object(
            runner, "prepare_event_file", return_value=Path(".github/events/push.json")
        ):
            cmd = runner.build_act_command(Path(".github/workflows/ci.yml"), job_filter="build")

            assert "--job" in cmd
            assert "build" in cmd

        # Test with custom image
        config = ValidationConfig.create(custom_image="custom-image")
        runner = ActRunner(config)

        with patch.object(
            runner, "prepare_event_file", return_value=Path(".github/events/push.json")
        ):
            cmd = runner.build_act_command(Path(".github/workflows/ci.yml"))

            assert "-P" in cmd
            assert "custom-image" in cmd

        # Test with verbose
        config = ValidationConfig.create(verbose=True)
        runner = ActRunner(config)

        with patch.object(
            runner, "prepare_event_file", return_value=Path(".github/events/push.json")
        ):
            cmd = runner.build_act_command(Path(".github/workflows/ci.yml"))

            assert "--verbose" in cmd

    @patch("subprocess.Popen")
    def test_run_workflow(self, mock_popen):
        """Test running workflow."""
        # Mock subprocess.Popen to return success
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        config = ValidationConfig.create()
        runner = ActRunner(config)

        # Test with success
        with patch.object(runner, "build_act_command", return_value=["act"]):
            success, error = runner.run_workflow(Path(".github/workflows/ci.yml"))

            assert success is True
            assert error is None
            mock_popen.assert_called_once()

        # Test with "Could not find any stages to run"
        mock_popen.reset_mock()
        mock_process.communicate.return_value = ("Could not find any stages to run", "")

        with patch.object(runner, "build_act_command", return_value=["act"]):
            success, error = runner.run_workflow(Path(".github/workflows/ci.yml"))

            assert success is True
            assert error is not None
            assert error.severity == ErrorSeverity.WARNING
            mock_popen.assert_called_once()

        # Test with failure
        mock_popen.reset_mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("Error: Workflow failed", "")

        with patch.object(runner, "build_act_command", return_value=["act"]):
            success, error = runner.run_workflow(Path(".github/workflows/ci.yml"))

            assert success is False
            assert error is not None
            assert error.severity == ErrorSeverity.ERROR
            mock_popen.assert_called_once()

        # Test with exception
        mock_popen.side_effect = Exception("Test exception")

        with patch.object(runner, "build_act_command", return_value=["act"]):
            success, error = runner.run_workflow(Path(".github/workflows/ci.yml"))

            assert success is False
            assert error is not None
            assert error.severity == ErrorSeverity.ERROR
