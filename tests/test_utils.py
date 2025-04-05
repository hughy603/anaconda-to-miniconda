"""Unit tests for the utility functions in conda_forge_converter.utils."""

import logging
import subprocess
from pathlib import Path
from unittest import mock
import pytest
from typing import Any

from conda_forge_converter.utils import (
    run_command,
    setup_logging,
    check_disk_space,
    is_conda_environment,
    is_command_output_str,
    set_log_level,
    logger,
)


@pytest.fixture
def reset_logger() -> None:
    """Reset the logger between tests."""
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    yield
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)


class TestRunCommand:
    """Tests for the run_command function."""

    @mock.patch("subprocess.run")
    def test_successful_command_with_capture(self, mock_run: mock.MagicMock) -> None:
        """Test running a command successfully with output capture."""
        # Setup
        mock_run.return_value = mock.Mock(stdout="command output", returncode=0)
        
        # Execute
        result = run_command(["echo", "test"], verbose=False)
        
        # Verify
        mock_run.assert_called_once_with(
            ["echo", "test"], capture_output=True, text=True, check=True
        )
        assert result == "command output"

    @mock.patch("subprocess.run")
    def test_successful_command_without_capture(self, mock_run: mock.MagicMock) -> None:
        """Test running a command successfully without output capture."""
        # Execute
        result = run_command(["echo", "test"], verbose=False, capture=False)
        
        # Verify
        mock_run.assert_called_once_with(["echo", "test"], check=True)
        assert result is True

    @mock.patch("subprocess.run")
    def test_failed_command(self, mock_run: mock.MagicMock) -> None:
        """Test running a command that fails."""
        # Setup
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["echo", "test"], stdout="", stderr="error output"
        )
        
        # Execute
        result = run_command(["echo", "test"], verbose=False)
        
        # Verify
        assert result is None

    @mock.patch("subprocess.run")
    def test_verbose_command(self, mock_run: mock.MagicMock, reset_logger: None) -> None:
        """Test running a command with verbose output."""
        # Setup
        mock_run.return_value = mock.Mock(stdout="command output", returncode=0)
        setup_logging(verbose=True)
        
        # Execute
        with mock.patch.object(logger, 'debug') as mock_debug:
            run_command(["echo", "test"], verbose=True)
        
        # Verify
        mock_debug.assert_called_once_with("Running: echo test")


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_default(self, reset_logger: None) -> None:
        """Test setting up logging with default settings."""
        # Execute
        setup_logging()
        
        # Verify
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_verbose(self, reset_logger: None) -> None:
        """Test setting up logging with verbose flag."""
        # Execute
        setup_logging(verbose=True)
        
        # Verify
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1

    def test_setup_logging_with_file(self, reset_logger: None, tmp_path: Any) -> None:
        """Test setting up logging with a log file."""
        # Setup
        log_file = tmp_path / "test.log"
        
        # Execute
        setup_logging(log_file=str(log_file))
        
        # Verify
        assert len(logger.handlers) == 2
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], logging.FileHandler)
        assert logger.handlers[1].baseFilename == str(log_file)


class TestCheckDiskSpace:
    """Tests for the check_disk_space function."""

    @mock.patch("shutil.disk_usage")
    def test_enough_disk_space(self, mock_disk_usage: mock.MagicMock) -> None:
        """Test when there is enough disk space."""
        # Setup
        mock_disk_usage.return_value = (1000 * 1024**3, 500 * 1024**3, 500 * 1024**3)  # 500GB free
        
        # Execute
        result = check_disk_space(needed_gb=10)
        
        # Verify
        assert result is True

    @mock.patch("shutil.disk_usage")
    def test_not_enough_disk_space(self, mock_disk_usage: mock.MagicMock, reset_logger: None) -> None:
        """Test when there is not enough disk space."""
        # Setup
        mock_disk_usage.return_value = (100 * 1024**3, 98 * 1024**3, 2 * 1024**3)  # 2GB free
        setup_logging()
        
        # Execute
        with mock.patch.object(logger, 'warning') as mock_warning:
            result = check_disk_space(needed_gb=10)
        
        # Verify
        assert result is False
        mock_warning.assert_called_once()


class TestIsCondaEnvironment:
    """Tests for the is_conda_environment function."""

    @mock.patch("pathlib.Path.exists")
    def test_valid_conda_environment(self, mock_exists: mock.MagicMock) -> None:
        """Test with a valid conda environment."""
        # Setup
        def mock_exists_implementation(path: Path) -> bool:
            # conda-meta exists, bin directory exists, python executable exists
            if str(path).endswith("conda-meta"):
                return True
            if str(path).endswith("bin"):
                return True
            if str(path).endswith("bin/python"):
                return True
            return False
        
        mock_exists.side_effect = mock_exists_implementation
        
        # Execute
        result = is_conda_environment("/path/to/env")
        
        # Verify
        assert result is True

    @mock.patch("pathlib.Path.exists")
    @mock.patch("sys.platform", "win32")  # Simulate Windows platform
    def test_valid_conda_environment_windows(self, mock_exists: mock.MagicMock) -> None:
        """Test with a valid conda environment on Windows."""
        # Setup
        def mock_exists_implementation(path: Path) -> bool:
            # conda-meta exists, Scripts directory exists, python.exe exists
            if str(path).endswith("conda-meta"):
                return True
            if str(path).endswith("Scripts"):
                return True
            if str(path).endswith("python.exe"):
                return True
            return False
        
        mock_exists.side_effect = mock_exists_implementation
        
        # Execute
        result = is_conda_environment("C:\\Users\\test\\anaconda3\\envs\\myenv")
        
        # Verify
        assert result is True


class TestIsCommandOutputStr:
    """Tests for the is_command_output_str function."""

    def test_with_string(self) -> None:
        """Test with a string value."""
        assert is_command_output_str("output") is True

    def test_with_none(self) -> None:
        """Test with None."""
        assert is_command_output_str(None) is False

    def test_with_bool(self) -> None:
        """Test with a boolean value."""
        assert is_command_output_str(True) is False


class TestSetLogLevel:
    """Tests for the set_log_level function."""

    def test_set_log_level(self, reset_logger: None) -> None:
        """Test setting various log levels."""
        # Setup
        setup_logging()
        
        # Execute & Verify
        set_log_level("DEBUG")
        assert logger.level == logging.DEBUG
        
        set_log_level("INFO")
        assert logger.level == logging.INFO
        
        set_log_level("WARNING")
        assert logger.level == logging.WARNING
        
        set_log_level("ERROR")
        assert logger.level == logging.ERROR
        
        set_log_level("CRITICAL")
        assert logger.level == logging.CRITICAL
