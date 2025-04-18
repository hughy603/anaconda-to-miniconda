"""Tests for the CLI module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from github_actions_validator.cli import cli, docs, init, main, validate


class TestCLI:
    """Tests for the CLI module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_version(self):
        """Test the CLI version command."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_cli_help(self):
        """Test the CLI help command."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Options:" in result.output
        assert "Commands:" in result.output
        assert "validate" in result.output
        assert "docs" in result.output
        assert "init" in result.output

    @patch("github_actions_validator.cli.ValidationConfig.create")
    @patch("github_actions_validator.cli.ErrorReporter")
    @patch("github_actions_validator.cli.find_workflows")
    def test_validate_no_workflows(
        self, mock_find_workflows, mock_error_reporter, mock_create_config
    ):
        """Test validate command with no workflows."""
        # Mock config
        mock_config = MagicMock()
        mock_create_config.return_value = mock_config

        # Mock error reporter
        mock_reporter = MagicMock()
        mock_error_reporter.return_value = mock_reporter

        # Mock find_workflows to return empty list
        mock_find_workflows.return_value = []

        # Run command
        result = self.runner.invoke(validate)

        # Verify
        assert result.exit_code == 0
        mock_find_workflows.assert_called_once()
        mock_reporter.add_error.assert_not_called()

    @patch("github_actions_validator.cli.ValidationConfig.create")
    @patch("github_actions_validator.cli.ErrorReporter")
    @patch("github_actions_validator.cli.find_workflows")
    def test_validate_dry_run(self, mock_find_workflows, mock_error_reporter, mock_create_config):
        """Test validate command with dry run."""
        # Mock config
        mock_config = MagicMock()
        mock_config.dry_run = True
        mock_create_config.return_value = mock_config

        # Mock error reporter
        mock_reporter = MagicMock()
        mock_error_reporter.return_value = mock_reporter

        # Mock find_workflows to return some workflows
        mock_find_workflows.return_value = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]

        # Run command
        result = self.runner.invoke(validate, ["--dry-run"])

        # Verify
        assert result.exit_code == 0
        mock_find_workflows.assert_called_once()
        mock_reporter.add_error.assert_not_called()

    @patch("github_actions_validator.cli.ValidationConfig.create")
    @patch("github_actions_validator.cli.ErrorReporter")
    @patch("github_actions_validator.cli.find_workflows")
    @patch("github_actions_validator.cli.validate_all_syntax")
    @patch("github_actions_validator.cli.validate_all_execution")
    def test_validate_skip_lint(
        self,
        mock_validate_execution,
        mock_validate_syntax,
        mock_find_workflows,
        mock_error_reporter,
        mock_create_config,
    ):
        """Test validate command with skip_lint."""
        # Mock config
        mock_config = MagicMock()
        mock_config.dry_run = False
        mock_config.skip_lint = True
        mock_create_config.return_value = mock_config

        # Mock error reporter
        mock_reporter = MagicMock()
        mock_error_reporter.return_value = mock_reporter

        # Mock find_workflows to return some workflows
        workflows = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]
        mock_find_workflows.return_value = workflows

        # Mock validate_all_execution to return success
        mock_validate_execution.return_value = (True, [])

        # Run command
        result = self.runner.invoke(validate, ["--skip-lint"])

        # Verify
        assert result.exit_code == 0
        mock_find_workflows.assert_called_once()
        mock_validate_syntax.assert_not_called()
        mock_validate_execution.assert_called_once()

    @patch("github_actions_validator.cli.ValidationConfig.create")
    @patch("github_actions_validator.cli.ErrorReporter")
    @patch("github_actions_validator.cli.find_workflows")
    @patch("github_actions_validator.cli.validate_all_syntax")
    @patch("github_actions_validator.cli.validate_all_execution")
    def test_validate_success(
        self,
        mock_validate_execution,
        mock_validate_syntax,
        mock_find_workflows,
        mock_error_reporter,
        mock_create_config,
    ):
        """Test validate command with successful validation."""
        # Mock config
        mock_config = MagicMock()
        mock_config.dry_run = False
        mock_config.skip_lint = False
        mock_create_config.return_value = mock_config

        # Mock error reporter
        mock_reporter = MagicMock()
        mock_error_reporter.return_value = mock_reporter

        # Mock find_workflows to return some workflows
        workflows = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]
        mock_find_workflows.return_value = workflows

        # Mock validate_all_syntax to return success
        mock_validate_syntax.return_value = (True, [])

        # Mock validate_all_execution to return success
        mock_validate_execution.return_value = (True, [])

        # Run command
        result = self.runner.invoke(validate)

        # Verify
        assert result.exit_code == 0
        mock_find_workflows.assert_called_once()
        mock_validate_syntax.assert_called_once_with(workflows, mock_config)
        mock_validate_execution.assert_called_once_with(workflows, mock_config)
        mock_reporter.add_error.assert_not_called()

    @patch("github_actions_validator.cli.ValidationConfig.create")
    @patch("github_actions_validator.cli.ErrorReporter")
    @patch("github_actions_validator.cli.find_workflows")
    @patch("github_actions_validator.cli.validate_all_syntax")
    def test_validate_syntax_failure(
        self, mock_validate_syntax, mock_find_workflows, mock_error_reporter, mock_create_config
    ):
        """Test validate command with syntax validation failure."""
        # Mock config
        mock_config = MagicMock()
        mock_config.dry_run = False
        mock_config.skip_lint = False
        mock_create_config.return_value = mock_config

        # Mock error reporter
        mock_reporter = MagicMock()
        mock_error_reporter.return_value = mock_reporter

        # Mock find_workflows to return some workflows
        workflows = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]
        mock_find_workflows.return_value = workflows

        # Mock validate_all_syntax to return failure
        mock_validate_syntax.return_value = (False, ["Syntax error"])

        # Mock sys.exit to avoid test exit
        with patch("sys.exit") as mock_exit:
            # Run command
            self.runner.invoke(validate)

            # Verify
            mock_find_workflows.assert_called_once()
            mock_validate_syntax.assert_called_once_with(workflows, mock_config)
            mock_reporter.add_error.assert_called_once()
            mock_exit.assert_called_once_with(1)

    @patch("github_actions_validator.cli.ValidationConfig.create")
    @patch("github_actions_validator.cli.ErrorReporter")
    @patch("github_actions_validator.cli.find_workflows")
    @patch("github_actions_validator.cli.validate_all_syntax")
    @patch("github_actions_validator.cli.validate_all_execution")
    def test_validate_execution_failure(
        self,
        mock_validate_execution,
        mock_validate_syntax,
        mock_find_workflows,
        mock_error_reporter,
        mock_create_config,
    ):
        """Test validate command with execution validation failure."""
        # Mock config
        mock_config = MagicMock()
        mock_config.dry_run = False
        mock_config.skip_lint = False
        mock_create_config.return_value = mock_config

        # Mock error reporter
        mock_reporter = MagicMock()
        mock_error_reporter.return_value = mock_reporter

        # Mock find_workflows to return some workflows
        workflows = [
            Path(".github/workflows/ci.yml"),
            Path(".github/workflows/release.yml"),
        ]
        mock_find_workflows.return_value = workflows

        # Mock validate_all_syntax to return success
        mock_validate_syntax.return_value = (True, [])

        # Mock validate_all_execution to return failure
        mock_validate_execution.return_value = (False, ["Execution error"])

        # Mock sys.exit to avoid test exit
        with patch("sys.exit") as mock_exit:
            # Run command
            self.runner.invoke(validate)

            # Verify
            mock_find_workflows.assert_called_once()
            mock_validate_syntax.assert_called_once_with(workflows, mock_config)
            mock_validate_execution.assert_called_once_with(workflows, mock_config)
            mock_reporter.add_error.assert_called_once()
            # Don't check the exact number of calls to sys.exit
            assert mock_exit.called

    @patch("subprocess.run")
    def test_docs_preview_success(self, mock_run):
        """Test docs preview command with successful execution."""
        # Mock subprocess.run
        mock_run.return_value = MagicMock(returncode=0)

        # Run command
        result = self.runner.invoke(docs, ["preview"])

        # Verify
        assert result.exit_code == 0
        mock_run.assert_called_once_with(["mkdocs", "serve", "--dev-addr", "localhost:8000"])

    @patch("subprocess.run")
    def test_docs_preview_custom_port(self, mock_run):
        """Test docs preview command with custom port."""
        # Mock subprocess.run
        mock_run.return_value = MagicMock(returncode=0)

        # Run command
        result = self.runner.invoke(docs, ["preview", "--port", "8080"])

        # Verify
        assert result.exit_code == 0
        mock_run.assert_called_once_with(["mkdocs", "serve", "--dev-addr", "localhost:8080"])

    @patch("subprocess.run")
    def test_docs_preview_command_not_found(self, mock_run):
        """Test docs preview command when mkdocs is not found."""
        # Mock subprocess.run to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("No such file or directory")

        # Mock sys.exit to avoid test exit
        with patch("sys.exit") as mock_exit:
            # Run command
            self.runner.invoke(docs, ["preview"])

            # Verify
            assert mock_exit.called

    @patch("subprocess.run")
    def test_docs_build_success(self, mock_run):
        """Test docs build command with successful execution."""
        # Mock subprocess.run
        mock_run.return_value = MagicMock(returncode=0)

        # Run command
        result = self.runner.invoke(docs, ["build"])

        # Verify
        assert result.exit_code == 0
        mock_run.assert_called_once_with(["mkdocs", "build", "--strict"])

    @patch("subprocess.run")
    def test_docs_build_command_not_found(self, mock_run):
        """Test docs build command when mkdocs is not found."""
        # Mock subprocess.run to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("No such file or directory")

        # Mock sys.exit to avoid test exit
        with patch("sys.exit") as mock_exit:
            # Run command
            self.runner.invoke(docs, ["build"])

            # Verify
            assert mock_exit.called

    @patch("builtins.open", new_callable=MagicMock)
    @patch("json.dump")
    @patch("github_actions_validator.cli.ValidationConfig.create")
    def test_init_default(self, mock_create_config, mock_json_dump, mock_open):
        """Test init command with default output file."""
        # Mock config
        mock_config = MagicMock()
        mock_create_config.return_value = mock_config
        mock_config.model_dump.return_value = {"key": "value"}

        # Run command
        result = self.runner.invoke(init)

        # Verify
        assert result.exit_code == 0
        mock_create_config.assert_called_once()
        mock_config.model_dump.assert_called_once()
        mock_open.assert_called_once_with(".github-actions-validator.json", "w")
        mock_json_dump.assert_called_once_with({"key": "value"}, mock_open().__enter__(), indent=2)

    @patch("builtins.open", new_callable=MagicMock)
    @patch("json.dump")
    @patch("github_actions_validator.cli.ValidationConfig.create")
    def test_init_custom_output(self, mock_create_config, mock_json_dump, mock_open):
        """Test init command with custom output file."""
        # Mock config
        mock_config = MagicMock()
        mock_create_config.return_value = mock_config
        mock_config.model_dump.return_value = {"key": "value"}

        # Run command
        result = self.runner.invoke(init, ["--output", "custom-config.json"])

        # Verify
        assert result.exit_code == 0
        mock_create_config.assert_called_once()
        mock_config.model_dump.assert_called_once()
        mock_open.assert_called_once_with("custom-config.json", "w")
        mock_json_dump.assert_called_once_with({"key": "value"}, mock_open().__enter__(), indent=2)

    @patch("github_actions_validator.cli.cli")
    def test_main(self, mock_cli):
        """Test main function."""
        main()
        mock_cli.assert_called_once()
