"""Tests for the actionlint validator module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from github_actions_validator.config import ValidationConfig
from github_actions_validator.validators.actionlint import validate_all_syntax, validate_syntax


class TestValidatorsActionlint:
    """Tests for the actionlint validator module."""

    def test_validate_syntax_skip_lint(self):
        """Test validate_syntax with skip_lint=True."""
        # Create config with skip_lint=True and verbose=True
        config = ValidationConfig.create(skip_lint=True, verbose=True)
        workflow_file = Path(".github/workflows/ci.yml")

        with patch("builtins.print") as mock_print:
            success, errors = validate_syntax(workflow_file, config)

            assert success is True
            assert len(errors) == 0
            # Use os.path.normpath to handle path separators correctly
            import os

            expected_path = os.path.normpath(".github/workflows/ci.yml")
            mock_print.assert_called_once_with(
                f"Skipping actionlint validation for {expected_path} (skip_lint is set)"
            )

    @patch("subprocess.run")
    def test_validate_syntax_actionlint_not_installed(self, mock_run):
        """Test validate_syntax when actionlint is not installed."""
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        # Mock subprocess.run to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("No such file or directory")

        with patch("builtins.print") as mock_print:
            success, errors = validate_syntax(workflow_file, config)

            assert success is False
            assert len(errors) == 1
            assert "actionlint not found" in errors[0]
            mock_print.assert_called_once()

    @patch("subprocess.run")
    def test_validate_syntax_actionlint_subprocess_error(self, mock_run):
        """Test validate_syntax when actionlint subprocess fails."""
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        # Mock subprocess.run to raise SubprocessError
        mock_run.side_effect = subprocess.SubprocessError("Subprocess error")

        with patch("builtins.print") as mock_print:
            success, errors = validate_syntax(workflow_file, config)

            assert success is False
            assert len(errors) == 1
            assert "actionlint not found" in errors[0]
            mock_print.assert_called_once()

    @patch("subprocess.run")
    def test_validate_syntax_success(self, mock_run):
        """Test validate_syntax with successful validation."""
        config = ValidationConfig.create(verbose=True)
        workflow_file = Path(".github/workflows/ci.yml")

        # Mock subprocess.run to return success
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        with patch("builtins.print") as mock_print:
            success, errors = validate_syntax(workflow_file, config)

            assert success is True
            assert len(errors) == 0
            mock_run.assert_called_with(
                ["actionlint", str(workflow_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            assert mock_print.call_count == 2
            # Use os.path.normpath to handle path separators correctly
            import os

            expected_path = os.path.normpath(".github/workflows/ci.yml")
            mock_print.assert_any_call(f"Running actionlint on {expected_path}")
            mock_print.assert_any_call(f"actionlint validation passed for {expected_path}")

    @patch("subprocess.run")
    def test_validate_syntax_failure(self, mock_run):
        """Test validate_syntax with failed validation."""
        config = ValidationConfig.create(verbose=True)
        workflow_file = Path(".github/workflows/ci.yml")

        # Mock subprocess.run to return failure
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = "Error: Invalid workflow file"
        mock_process.stderr = ".github/workflows/ci.yml:10: error: Invalid syntax"
        mock_run.return_value = mock_process

        with patch("builtins.print") as mock_print:
            success, errors = validate_syntax(workflow_file, config)

            assert success is False
            assert len(errors) == 2
            assert "Error: Invalid workflow file" in errors
            assert ".github/workflows/ci.yml:10: error: Invalid syntax" in errors
            mock_run.assert_called_with(
                ["actionlint", str(workflow_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            assert mock_print.call_count == 2
            # Use os.path.normpath to handle path separators correctly
            import os

            expected_path = os.path.normpath(".github/workflows/ci.yml")
            mock_print.assert_any_call(f"Running actionlint on {expected_path}")
            mock_print.assert_any_call(f"actionlint found 2 errors in {expected_path}")

    @patch("subprocess.run")
    def test_validate_syntax_exception(self, mock_run):
        """Test validate_syntax with exception."""
        config = ValidationConfig.create()
        workflow_file = Path(".github/workflows/ci.yml")

        # Set up the mock to raise an exception only for the first call (--version check)
        # but return a normal result for subsequent calls
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.side_effect = [subprocess.SubprocessError("Command failed"), mock_process]

        with patch("builtins.print") as mock_print:
            success, errors = validate_syntax(workflow_file, config)

            assert success is False
            assert len(errors) == 1
            assert "actionlint not found" in errors[0]
            mock_print.assert_called_once()
            mock_print.assert_called_once_with(
                "actionlint not found. Please install actionlint: https://github.com/rhysd/actionlint#installation"
            )

    @patch("github_actions_validator.validators.actionlint.validate_syntax")
    def test_validate_all_syntax_all_success(self, mock_validate_syntax):
        """Test validate_all_syntax with all successful validations."""
        config = ValidationConfig.create()
        workflow_files = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]

        # Mock validate_syntax to return success for all files
        mock_validate_syntax.return_value = (True, [])

        success, errors = validate_all_syntax(workflow_files, config)

        assert success is True
        assert len(errors) == 0
        assert mock_validate_syntax.call_count == 2
        mock_validate_syntax.assert_any_call(workflow_files[0], config)
        mock_validate_syntax.assert_any_call(workflow_files[1], config)

    @patch("github_actions_validator.validators.actionlint.validate_syntax")
    def test_validate_all_syntax_some_failures(self, mock_validate_syntax):
        """Test validate_all_syntax with some failed validations."""
        config = ValidationConfig.create()
        workflow_files = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]

        # Mock validate_syntax to return success for first file and failure for second
        mock_validate_syntax.side_effect = [
            (True, []),
            (False, ["Error in release.yml"]),
        ]

        success, errors = validate_all_syntax(workflow_files, config)

        assert success is False
        assert len(errors) == 1
        assert "Error in release.yml" in errors
        assert mock_validate_syntax.call_count == 2
        mock_validate_syntax.assert_any_call(workflow_files[0], config)
        mock_validate_syntax.assert_any_call(workflow_files[1], config)

    @patch("github_actions_validator.validators.actionlint.validate_syntax")
    def test_validate_all_syntax_all_failures(self, mock_validate_syntax):
        """Test validate_all_syntax with all failed validations."""
        config = ValidationConfig.create()
        workflow_files = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]

        # Mock validate_syntax to return failure for all files
        mock_validate_syntax.side_effect = [
            (False, ["Error in ci.yml"]),
            (False, ["Error in release.yml"]),
        ]

        success, errors = validate_all_syntax(workflow_files, config)

        assert success is False
        assert len(errors) == 2
        assert "Error in ci.yml" in errors
        assert "Error in release.yml" in errors
        assert mock_validate_syntax.call_count == 2
        mock_validate_syntax.assert_any_call(workflow_files[0], config)
        mock_validate_syntax.assert_any_call(workflow_files[1], config)
