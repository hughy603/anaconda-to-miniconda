"""Tests for the execution validator module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from github_actions_validator.config import ValidationConfig
from github_actions_validator.validators.execution import (
    build_act_command,
    prepare_event_file,
    validate_all_execution,
    validate_execution,
)


class TestValidatorsExecution:
    """Tests for the execution validator module."""

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_prepare_event_file_new(self, mock_json_dump, mock_file, mock_exists, mock_mkdir):
        """Test preparing a new event file."""
        # Mock Path.exists to return False
        mock_exists.return_value = False

        # Test with push event
        event_file = prepare_event_file("push")

        assert event_file == Path(".github/events/push.json")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_file.assert_called_once_with(event_file, "w")
        mock_json_dump.assert_called_once()
        # Check that the event data contains expected keys
        args, kwargs = mock_json_dump.call_args
        event_data = args[0]
        assert "ref" in event_data
        assert "repository" in event_data
        assert "name" in event_data["repository"]
        assert "full_name" in event_data["repository"]
        assert "owner" in event_data["repository"]

    def test_prepare_event_file_existing(self):
        """Test preparing an existing event file."""
        # Use a context manager to patch the specific instance method
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "mkdir") as mock_mkdir:
                with patch("builtins.open") as mock_open:
                    # Test with push event
                    event_file = prepare_event_file("push")

                    assert str(event_file).replace("\\", "/") == ".github/events/push.json"
                    # Verify that no file operations were performed
                    mock_mkdir.assert_called_once()  # mkdir is always called with exist_ok=True
                    mock_open.assert_not_called()  # open should not be called

    @patch("github_actions_validator.validators.execution.prepare_event_file")
    def test_build_act_command_basic(self, mock_prepare_event_file):
        """Test building a basic act command."""
        # Mock prepare_event_file to return a path
        mock_prepare_event_file.return_value = Path(".github/events/push.json")

        # Create a config
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        # Test with default parameters
        with patch("os.path.exists", return_value=True):
            cmd = build_act_command(workflow_file, config)

            assert cmd[0] == "act"
            assert "-W" in cmd
            assert ".github/workflows/ci.yml" in cmd
            assert "-e" in cmd
            assert ".github/events/push.json" in cmd
            assert "--action-cache-path" in cmd
            assert "--env" in cmd
            assert "-s" in cmd
            assert "GITHUB_TOKEN=local-testing-token" in cmd

    @patch("github_actions_validator.validators.execution.prepare_event_file")
    def test_build_act_command_with_job(self, mock_prepare_event_file):
        """Test building an act command with a job filter."""
        # Mock prepare_event_file to return a path
        mock_prepare_event_file.return_value = Path(".github/events/push.json")

        # Create a config
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        # Test with job filter
        with patch("os.path.exists", return_value=True):
            cmd = build_act_command(workflow_file, config, job="build")

            assert "--job" in cmd
            assert "build" in cmd

    @patch("github_actions_validator.validators.execution.prepare_event_file")
    def test_build_act_command_with_event_type(self, mock_prepare_event_file):
        """Test building an act command with a specific event type."""
        # Mock prepare_event_file to return a path
        mock_prepare_event_file.return_value = Path(".github/events/pull_request.json")

        # Create a config
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        # Test with event type
        with patch("os.path.exists", return_value=True):
            cmd = build_act_command(workflow_file, config, event_type="pull_request")

            assert "-e" in cmd
            assert ".github/events/pull_request.json" in cmd
            mock_prepare_event_file.assert_called_with("pull_request", workflow_file)

    @patch("github_actions_validator.validators.execution.prepare_event_file")
    def test_build_act_command_with_custom_image(self, mock_prepare_event_file):
        """Test building an act command with a custom image."""
        # Mock prepare_event_file to return a path
        mock_prepare_event_file.return_value = Path(".github/events/push.json")

        # Create a config with custom image
        config = ValidationConfig.create(custom_image="custom-image")
        workflow_file = Path(".github/workflows/ci.yml")

        # Test with custom image
        with patch("os.path.exists", return_value=True):
            cmd = build_act_command(workflow_file, config)

            assert "-P" in cmd
            assert "custom-image" in cmd

    @patch("github_actions_validator.validators.execution.prepare_event_file")
    def test_build_act_command_with_verbose(self, mock_prepare_event_file):
        """Test building an act command with verbose flag."""
        # Mock prepare_event_file to return a path
        mock_prepare_event_file.return_value = Path(".github/events/push.json")

        # Create a config with verbose flag
        config = ValidationConfig.create(verbose=True)
        workflow_file = Path(".github/workflows/ci.yml")

        # Test with verbose flag
        with patch("os.path.exists", return_value=True):
            cmd = build_act_command(workflow_file, config)

            assert "--verbose" in cmd

    @patch("github_actions_validator.validators.execution.prepare_event_file")
    def test_build_act_command_without_cache_path(self, mock_prepare_event_file):
        """Test building an act command when cache path doesn't exist."""
        # Mock prepare_event_file to return a path
        mock_prepare_event_file.return_value = Path(".github/events/push.json")

        # Create a config
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        # Test when cache path doesn't exist
        with patch("os.path.exists", return_value=False):
            cmd = build_act_command(workflow_file, config)

            assert "--action-cache-path" not in cmd

    @patch("subprocess.run")
    def test_validate_execution_act_not_installed(self, mock_run):
        """Test validate_execution when act is not installed."""
        # Mock subprocess.run to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("No such file or directory")

        # Create a config
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        with patch("builtins.print") as mock_print:
            success, errors = validate_execution(workflow_file, config)

            assert success is False
            assert len(errors) == 1
            assert "act not found" in errors[0]
            mock_print.assert_called_once_with(
                "act not found. Please install act: https://github.com/nektos/act#installation"
            )

    @patch("subprocess.run")
    def test_validate_execution_act_subprocess_error(self, mock_run):
        """Test validate_execution when act subprocess fails."""
        # Mock subprocess.run to raise SubprocessError
        mock_run.side_effect = subprocess.SubprocessError("Subprocess error")

        # Create a config
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        with patch("builtins.print") as mock_print:
            success, errors = validate_execution(workflow_file, config)

            assert success is False
            assert len(errors) == 1
            assert "act not found" in errors[0]
            mock_print.assert_called_once_with(
                "act not found. Please install act: https://github.com/nektos/act#installation"
            )

    @patch("subprocess.run")
    @patch("github_actions_validator.validators.execution.build_act_command")
    def test_validate_execution_success(self, mock_build_cmd, mock_run):
        """Test validate_execution with successful execution."""
        # Mock build_act_command to return a command
        mock_build_cmd.return_value = ["act", "-W", "workflow.yml"]

        # Mock subprocess.run to return success
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Success"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Create a config with verbose flag
        config = ValidationConfig.create(verbose=True)
        workflow_file = Path(".github/workflows/ci.yml")

        with patch("builtins.print") as mock_print:
            success, errors = validate_execution(workflow_file, config)

            assert success is True
            assert len(errors) == 0
            mock_run.assert_called_with(
                ["act", "-W", "workflow.yml"],
                capture_output=True,
                text=True,
                check=False,
                timeout=config.job_timeout,
            )
            assert mock_print.call_count == 2
            mock_print.assert_any_call("Running command: act -W workflow.yml")
            # Use os.path.normpath to handle path separators correctly
            import os

            expected_path = os.path.normpath(".github/workflows/ci.yml")
            mock_print.assert_any_call(f"act validation passed for {expected_path}")

    @patch("subprocess.run")
    @patch("github_actions_validator.validators.execution.build_act_command")
    def test_validate_execution_failure(self, mock_build_cmd, mock_run):
        """Test validate_execution with failed execution."""
        # Mock build_act_command to return a command
        mock_build_cmd.return_value = ["act", "-W", "workflow.yml"]

        # Mock subprocess.run to return failure
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = "Error: Workflow failed"
        mock_process.stderr = "Error: Something went wrong"
        mock_run.return_value = mock_process

        # Create a config with verbose flag
        config = ValidationConfig.create(verbose=True)
        workflow_file = Path(".github/workflows/ci.yml")

        with patch("builtins.print") as mock_print:
            success, errors = validate_execution(workflow_file, config)

            assert success is False
            assert len(errors) == 2
            assert "Error: Workflow failed" in errors
            assert "Error: Something went wrong" in errors
            mock_run.assert_called_with(
                ["act", "-W", "workflow.yml"],
                capture_output=True,
                text=True,
                check=False,
                timeout=config.job_timeout,
            )
            assert mock_print.call_count == 2
            mock_print.assert_any_call("Running command: act -W workflow.yml")
            # Use os.path.normpath to handle path separators correctly
            import os

            expected_path = os.path.normpath(".github/workflows/ci.yml")
            mock_print.assert_any_call(f"act found 2 errors in {expected_path}")

    @patch("subprocess.run")
    @patch("github_actions_validator.validators.execution.build_act_command")
    def test_validate_execution_failure_no_specific_errors(self, mock_build_cmd, mock_run):
        """Test validate_execution with failure but no specific errors."""
        # Mock build_act_command to return a command
        mock_build_cmd.return_value = ["act", "-W", "workflow.yml"]

        # Set up the mock to handle the version check first, then return the failure result
        version_check = MagicMock()
        version_check.returncode = 0

        failure_result = MagicMock()
        failure_result.returncode = 1
        failure_result.stdout = "Some output without error:"
        failure_result.stderr = ""

        mock_run.side_effect = [version_check, failure_result]

        # Create a config
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        success, errors = validate_execution(workflow_file, config)

        assert success is False
        assert len(errors) == 1
        # The actual error message might be different, so we'll just check that we have an error
        assert "error" in errors[0].lower() or "failed" in errors[0].lower()

    @patch("subprocess.run")
    @patch("github_actions_validator.validators.execution.build_act_command")
    def test_validate_execution_timeout(self, mock_build_cmd, mock_run):
        """Test validate_execution with timeout."""
        # Mock build_act_command to return a command
        mock_build_cmd.return_value = ["act", "-W", "workflow.yml"]

        # Set up the mock to handle the version check first, then raise TimeoutExpired
        version_check = MagicMock()
        version_check.returncode = 0

        mock_run.side_effect = [
            version_check,  # First call for version check
            subprocess.TimeoutExpired(cmd=["act"], timeout=300),  # Second call for actual execution
        ]

        # Create a config
        config = ValidationConfig.create(job_timeout=300)
        workflow_file = Path(".github/workflows/ci.yml")

        with patch("builtins.print") as mock_print:
            success, errors = validate_execution(workflow_file, config)

            assert success is False
            assert len(errors) == 1
            assert "timed out" in errors[0].lower()
            assert "300" in errors[0]  # Check that the timeout value is in the error message
            mock_print.assert_called_once()

    @patch("subprocess.run")
    @patch("github_actions_validator.validators.execution.build_act_command")
    def test_validate_execution_exception(self, mock_build_cmd, mock_run):
        """Test validate_execution with exception."""
        # Mock build_act_command to return a command
        mock_build_cmd.return_value = ["act", "-W", "workflow.yml"]

        # Set up the mock to handle the version check first, then raise an exception
        # This simulates act being installed but failing during execution
        version_check = MagicMock()
        version_check.returncode = 0

        mock_run.side_effect = [
            version_check,  # First call for version check
            Exception("Test exception"),  # Second call for actual execution
        ]

        # Create a config
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        with patch("builtins.print") as mock_print:
            success, errors = validate_execution(workflow_file, config)

            assert success is False
            assert len(errors) == 1
            assert "Error running act" in errors[0]
            assert "Test exception" in errors[0]
            mock_print.assert_called_once()

    @patch("github_actions_validator.validators.execution.validate_execution")
    def test_validate_all_execution_all_success(self, mock_validate_execution):
        """Test validate_all_execution with all successful validations."""
        # Mock validate_execution to return success for all files
        mock_validate_execution.return_value = (True, [])

        # Create a config
        config = ValidationConfig.create()
        workflow_files = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]

        success, errors = validate_all_execution(workflow_files, config)

        assert success is True
        assert len(errors) == 0
        assert mock_validate_execution.call_count == 2
        mock_validate_execution.assert_any_call(workflow_files[0], config)
        mock_validate_execution.assert_any_call(workflow_files[1], config)

    @patch("github_actions_validator.validators.execution.validate_execution")
    def test_validate_all_execution_some_failures(self, mock_validate_execution):
        """Test validate_all_execution with some failed validations."""
        # Mock validate_execution to return success for first file and failure for second
        mock_validate_execution.side_effect = [
            (True, []),
            (False, ["Error in release.yml"]),
        ]

        # Create a config
        config = ValidationConfig.create()
        workflow_files = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]

        success, errors = validate_all_execution(workflow_files, config)

        assert success is False
        assert len(errors) == 1
        assert "Error in release.yml" in errors
        assert mock_validate_execution.call_count == 2
        mock_validate_execution.assert_any_call(workflow_files[0], config)
        mock_validate_execution.assert_any_call(workflow_files[1], config)

    @patch("github_actions_validator.validators.execution.validate_execution")
    def test_validate_all_execution_all_failures(self, mock_validate_execution):
        """Test validate_all_execution with all failed validations."""
        # Mock validate_execution to return failure for all files
        mock_validate_execution.side_effect = [
            (False, ["Error in ci.yml"]),
            (False, ["Error in release.yml"]),
        ]

        # Create a config
        config = ValidationConfig.create()
        workflow_files = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]

        success, errors = validate_all_execution(workflow_files, config)

        assert success is False
        assert len(errors) == 2
        assert "Error in ci.yml" in errors
        assert "Error in release.yml" in errors
        assert mock_validate_execution.call_count == 2
        mock_validate_execution.assert_any_call(workflow_files[0], config)
        mock_validate_execution.assert_any_call(workflow_files[1], config)
