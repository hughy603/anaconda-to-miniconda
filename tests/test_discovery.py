"""Tests for the discovery module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from github_actions_validator.discovery import extract_jobs, find_workflows


class TestDiscovery:
    """Tests for the discovery module."""

    @patch("pathlib.Path.exists")
    def test_find_workflows_specific_file(self, mock_exists):
        """Test finding a specific workflow file."""
        # Mock the exists method to return True
        mock_exists.return_value = True

        # Test finding a specific workflow file
        workflows = find_workflows(workflow_file="ci.yml")
        assert len(workflows) == 1
        assert workflows[0] == Path("ci.yml")

        # Test finding a specific workflow file with workflows directory prefix
        workflows = find_workflows(workflow_file="release.yml")
        assert len(workflows) == 1
        assert workflows[0] == Path("release.yml")

    @patch("pathlib.Path.exists")
    def test_find_workflows_specific_file_not_found(self, mock_exists):
        """Test finding a specific workflow file that doesn't exist."""
        # Mock the exists method to return False
        mock_exists.return_value = False

        # Test finding a specific workflow file that doesn't exist
        with patch("builtins.print") as mock_print:
            workflows = find_workflows(workflow_file="nonexistent.yml")
            assert len(workflows) == 0
            mock_print.assert_called_once_with("Warning: Workflow file not found: nonexistent.yml")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_find_workflows_directory_not_found(self, mock_is_dir, mock_exists):
        """Test finding workflows when the directory doesn't exist."""
        # Mock the exists method to return True but is_dir to return False
        mock_exists.return_value = True
        mock_is_dir.return_value = False

        # Test finding workflows when the directory doesn't exist
        with patch("builtins.print") as mock_print:
            workflows = find_workflows()
            assert len(workflows) == 0
            mock_print.assert_called_once_with(
                "Warning: Workflows directory not found: .github/workflows"
            )

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.glob")
    @patch("subprocess.run")
    def test_find_workflows_changed_only(self, mock_run, mock_glob, mock_is_dir, mock_exists):
        """Test finding only changed workflow files."""
        # Mock the exists and is_dir methods to return True
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Mock the glob method to return a list of workflow files
        mock_glob.side_effect = [
            [Path(".github/workflows/ci.yml"), Path(".github/workflows/release.yml")],
            [],  # No yaml files
        ]

        # Mock the subprocess.run method to return a list of changed files
        mock_process = MagicMock()
        mock_process.stdout = ".github/workflows/ci.yml\n"
        mock_run.return_value = mock_process

        # Test finding only changed workflow files
        workflows = find_workflows(changed_only=True)
        assert len(workflows) == 1
        assert workflows[0] == Path(".github/workflows/ci.yml")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.glob")
    @patch("subprocess.run")
    def test_find_workflows_changed_only_subprocess_error(
        self, mock_run, mock_glob, mock_is_dir, mock_exists
    ):
        """Test finding changed workflow files when subprocess fails."""
        # Mock the exists and is_dir methods to return True
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Mock the glob method to return a list of workflow files
        mock_glob.side_effect = [
            [Path(".github/workflows/ci.yml"), Path(".github/workflows/release.yml")],
            [],  # No yaml files
        ]

        # Mock the subprocess.run method to raise an error
        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        # Test finding changed workflow files when subprocess fails
        with patch("builtins.print") as mock_print:
            workflows = find_workflows(changed_only=True)
            assert len(workflows) == 2
            mock_print.assert_called_once_with(
                "Warning: Could not determine changed files. Using all workflow files."
            )

    @patch("builtins.open", new_callable=MagicMock)
    def test_extract_jobs_import_error(self, mock_open):
        """Test extracting jobs when yaml module is not available."""
        # Mock the import to raise ImportError
        with patch("yaml.safe_load", side_effect=ImportError("No module named 'yaml'")):
            workflow_file = Path(".github/workflows/ci.yml")
            jobs = extract_jobs(workflow_file)
            assert len(jobs) == 0
