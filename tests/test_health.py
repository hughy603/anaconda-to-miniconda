"""Tests for the health module."""

from unittest import mock

from conda_forge_converter.health import (
    _check_environment_exists,
    _check_python_version,
    _test_run_python,
    check_environment_health,
    verify_environment,
)


class TestHealthCheck:
    """Tests for the health check functionality."""

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_exists(self, mock_run: mock.MagicMock) -> None:
        """Test checking if an environment exists."""
        # Setup
        mock_run.return_value = '{"envs": ["/path/to/base", "/path/to/envs/myenv"]}'

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_exists("myenv", result, False)

        # Verify
        assert result["status"] == "GOOD"
        assert not result["issues"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_not_found(self, mock_run: mock.MagicMock) -> None:
        """Test checking a non-existent environment."""
        # Setup
        mock_run.return_value = '{"envs": ["/path/to/base", "/path/to/envs/myenv"]}'

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_exists("missing_env", result, False)

        # Verify
        assert result["status"] == "ERROR"
        assert len(result["issues"]) == 1
        assert "does not exist" in result["issues"][0]["message"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_python_version(self, mock_run: mock.MagicMock) -> None:
        """Test checking Python version."""
        # Setup
        mock_run.return_value = (
            '[{"name": "python", "version": "3.11.3", "channel": "conda-forge"}]'
        )

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_python_version("myenv", result, False)

        # Verify
        assert result["status"] == "GOOD"
        assert not result["issues"]
        assert result["details"]["python_version"] == "3.11.3"

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_python_eol(self, mock_run: mock.MagicMock) -> None:
        """Test checking EOL Python version."""
        # Setup
        mock_run.return_value = (
            '[{"name": "python", "version": "3.7.12", "channel": "conda-forge"}]'
        )

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_python_version("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "end-of-life" in result["issues"][0]["message"]
        assert result["details"]["python_version"] == "3.7.12"

    def test_full_health_check(self) -> None:
        """Test the full health check function."""
        # Use direct patching of individual check functions instead of the main function
        with (
            mock.patch(
                "conda_forge_converter.health._check_environment_exists"
            ) as mock_check_exists,
            mock.patch("conda_forge_converter.health._check_python_version") as mock_check_python,
            mock.patch(
                "conda_forge_converter.health._check_environment_packages"
            ) as mock_check_pkgs,
            mock.patch(
                "conda_forge_converter.health._check_environment_conflicts"
            ) as mock_check_conflicts,
            mock.patch("conda_forge_converter.health._check_environment_size") as mock_check_size,
        ):
            # Setup the mocks to do nothing (they update the result dict in-place)
            def mock_check(_env_name, result, _verbose):
                result["name"] = "myenv"
                result["status"] = "GOOD"
                result["details"]["python_version"] = "3.11.3"

            mock_check_exists.side_effect = mock_check

            # Execute
            result = check_environment_health("myenv", False)

            # Verify
            assert result["status"] == "GOOD"
            assert "name" in result
            assert "details" in result

    @mock.patch("conda_forge_converter.health.run_command")
    @mock.patch("conda_forge_converter.health._test_imports")
    @mock.patch("conda_forge_converter.health._test_run_python")
    @mock.patch("conda_forge_converter.health._test_pip")
    def test_verify_environment(
        self,
        mock_test_pip: mock.MagicMock,
        mock_test_python: mock.MagicMock,
        mock_test_imports: mock.MagicMock,
        mock_run: mock.MagicMock,
    ) -> None:
        """Test verifying environment functionality."""
        # Setup for successful test
        mock_test_imports.return_value = True
        mock_test_python.return_value = True
        mock_test_pip.return_value = True

        # Execute
        result = verify_environment("myenv", tests=["run_python", "test_pip"])

        # Verify
        assert result is True
        assert mock_test_python.call_count == 1
        assert mock_test_pip.call_count == 1
        assert mock_test_imports.call_count == 0  # Not in the requested tests

    @mock.patch("conda_forge_converter.health.run_command")
    @mock.patch("conda_forge_converter.health._test_run_python")
    def test_verify_environment_failure(
        self, mock_test_python: mock.MagicMock, mock_run: mock.MagicMock
    ) -> None:
        """Test verifying environment with failure."""
        # Setup for failed test
        mock_test_python.return_value = False

        # Execute
        result = verify_environment("myenv", tests=["run_python"])

        # Verify
        assert result is False
        assert mock_test_python.call_count == 1

    @mock.patch("conda_forge_converter.health.run_command")
    def test_python_execution(self, mock_run: mock.MagicMock) -> None:
        """Test running Python in the environment."""
        # Setup
        mock_run.return_value = "Hello, World!"

        # Execute
        result = _test_run_python("myenv", False)

        # Verify
        assert result is True
        mock_run.assert_called_once()
