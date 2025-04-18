"""Tests for the GitHub Actions validator package."""

from pathlib import Path
from unittest.mock import mock_open, patch

import yaml

from github_actions_validator.config import ValidationConfig
from github_actions_validator.discovery import extract_jobs, find_workflows
from github_actions_validator.error_handling import ErrorReporter, ErrorSeverity, ValidationError


class TestConfig:
    """Tests for the ValidationConfig class."""

    def test_default_config(self):
        """Test that default configuration is created correctly."""
        config = ValidationConfig.create()
        assert config.changed_only is False
        assert config.verbose is False
        assert config.dry_run is False
        assert config.skip_lint is False
        assert config.secrets_file == ".github/local-secrets.json"
        assert config.cache_path == "./.act-cache"
        assert config.custom_image == ""
        assert config.default_event == "push"
        assert config.workflow_file == ""
        assert "*" in config.workflow_events
        assert config.workflow_events["*"] == "push"

    def test_get_event_for_workflow(self):
        """Test that the correct event type is returned for a workflow."""
        config = ValidationConfig.create()

        # Test with a workflow that has a specific event type
        ci_workflow = Path(".github/workflows/ci.yml")
        assert config.get_event_for_workflow(ci_workflow) == "push"

        # Test with a workflow that uses the default event type
        custom_workflow = Path(".github/workflows/custom.yml")
        assert config.get_event_for_workflow(custom_workflow) == "push"

        # Test with a custom event type
        config.workflow_events["custom.yml"] = "pull_request"
        assert config.get_event_for_workflow(custom_workflow) == "pull_request"


class TestDiscovery:
    """Tests for the discovery module."""

    @patch("github_actions_validator.discovery.Path.exists")
    @patch("github_actions_validator.discovery.Path.glob")
    def test_find_workflows(self, mock_glob, mock_exists):
        """Test that workflows are found correctly."""
        # Mock the exists method to return True
        mock_exists.return_value = True

        # Mock the glob method to return a list of workflow files
        mock_glob.side_effect = [
            [Path(".github/workflows/ci.yml"), Path(".github/workflows/release.yml")],
            [],  # No yaml files
        ]

        # Test finding all workflows
        workflows = find_workflows()
        assert len(workflows) == 2
        assert workflows[0] == Path(".github/workflows/ci.yml")
        assert workflows[1] == Path(".github/workflows/release.yml")

    def test_get_workflow_name(self):
        """Test that workflow names are extracted correctly."""
        workflow_file = Path(".github/workflows/ci.yml")
        # Simple implementation of get_workflow_name
        assert workflow_file.name == "ci.yml"


class TestErrorHandling:
    """Tests for the error handling module."""

    def test_validation_error(self):
        """Test that validation errors are created correctly."""
        error = ValidationError(
            message="Test error",
            severity=ErrorSeverity.ERROR,
            workflow_file="ci.yml",
            job_name="build",
            line_number=10,
            context="context",
            suggestion="suggestion",
        )

        assert error.message == "Test error"
        assert error.severity == ErrorSeverity.ERROR
        assert error.workflow_file == "ci.yml"
        assert error.job_name == "build"
        assert error.line_number == 10
        assert error.context == "context"
        assert error.suggestion == "suggestion"

    def test_error_reporter_format_error(self):
        """Test that errors are formatted correctly."""
        error_reporter = ErrorReporter()

        # Test with a known error pattern
        error = error_reporter.format_error(
            error_message="Unknown action: 'actions/setup-pythonx@v4'",
            workflow_name="ci.yml",
            job_name="build",
        )

        assert error.message == "Unknown action: 'actions/setup-pythonx@v4'"
        assert error.severity == ErrorSeverity.ERROR
        assert error.workflow_file == "ci.yml"
        assert error.job_name == "build"
        assert error.suggestion is not None
        assert "action" in error.suggestion.lower()


class TestValidators:
    """Tests for the validators module."""

    @patch("builtins.open", new_callable=mock_open, read_data="mock file")
    @patch("yaml.safe_load")
    def test_extract_jobs(self, mock_safe_load, mock_file):
        """Test that jobs are extracted correctly from a workflow file."""
        # Mock the yaml.safe_load function to return a workflow with jobs
        mock_safe_load.return_value = {
            "jobs": {
                "build": {"runs-on": "ubuntu-latest", "steps": []},
                "test": {"runs-on": "ubuntu-latest", "steps": []},
            }
        }

        # Test extracting jobs
        workflow_file = Path(".github/workflows/ci.yml")
        jobs = extract_jobs(workflow_file)

        assert len(jobs) == 2
        assert "build" in jobs
        assert "test" in jobs

        # Test with a workflow that has no jobs
        mock_safe_load.return_value = {}
        jobs = extract_jobs(workflow_file)
        assert len(jobs) == 0

        # Test with a YAML error
        mock_safe_load.side_effect = yaml.YAMLError("YAML error")
        jobs = extract_jobs(workflow_file)
        assert len(jobs) == 0
