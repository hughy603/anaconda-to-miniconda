"""Tests for the health module."""

import json
from pathlib import Path
from unittest import mock

# Import everything at the module level
from conda_forge_converter.health import (
    _calculate_directory_size,
    _check_environment_conflicts,
    _check_environment_exists,
    _check_environment_packages,
    _check_environment_size,
    _check_python_version,
    _test_imports,
    _test_pip,
    _test_run_python,
    check_duplicate_packages,
    check_environment_health,
    check_package_conflicts,
    check_package_imports,
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
    def test_check_environment_exists_command_failure(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment existence when command fails."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_exists("myenv", result, False)

        # Verify
        assert result["status"] == "ERROR"
        assert len(result["issues"]) == 1
        assert isinstance(result["issues"], list)
        assert any(
            "Failed to list conda environments" in issue["message"] for issue in result["issues"]
        )

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_exists_invalid_json(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment existence with invalid JSON response."""
        # Setup
        mock_run.return_value = "Invalid JSON"  # Not valid JSON

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_exists("myenv", result, False)

        # Verify
        assert result["status"] == "ERROR"
        assert len(result["issues"]) == 1
        assert "Could not parse conda environment list output" in result["issues"][0]["message"]

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

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_python_version_command_failure(self, mock_run: mock.MagicMock) -> None:
        """Test checking Python version when command fails."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_python_version("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "Could not determine Python version" in result["issues"][0]["message"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_python_version_no_python(self, mock_run: mock.MagicMock) -> None:
        """Test checking Python version when Python is not found."""
        # Setup
        mock_run.return_value = "[]"  # No Python package found

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_python_version("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "Python not found in environment" in result["issues"][0]["message"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_python_version_invalid_json(self, mock_run: mock.MagicMock) -> None:
        """Test checking Python version with invalid JSON response."""
        # Setup
        mock_run.return_value = "Invalid JSON"  # Not valid JSON

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_python_version("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "Error checking Python version" in result["issues"][0]["message"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_packages(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment packages."""
        # Setup
        mock_run.return_value = json.dumps(
            [
                {"name": "python", "version": "3.11.3", "channel": "conda-forge"},
                {"name": "numpy", "version": "1.24.3", "channel": "conda-forge"},
                {"name": "pandas", "version": "2.0.1", "channel": "conda-forge"},
                {"name": "requests", "version": "2.28.2", "channel": "pypi"},
            ]
        )

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_packages("myenv", result, False)

        # Verify
        assert result["status"] == "GOOD"
        assert not result["issues"]
        assert result["details"]["package_counts"]["conda"] == 3
        assert result["details"]["package_counts"]["pip"] == 1
        assert result["details"]["package_counts"]["total"] == 4

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_packages_large_env(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment with a large number of packages."""
        # Setup
        # Create a list of 201 packages (exceeding the 200 threshold)
        packages = [
            {"name": f"package{i}", "version": "1.0.0", "channel": "conda-forge"}
            for i in range(201)
        ]
        mock_run.return_value = json.dumps(packages)

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_packages("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "very large number of packages" in result["issues"][0]["message"]
        assert result["details"]["package_counts"]["total"] == 201

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_packages_command_failure(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment packages when command fails."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_packages("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "Could not list packages in environment" in result["issues"][0]["message"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_packages_invalid_json(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment packages with invalid JSON response."""
        # Setup
        mock_run.return_value = "Invalid JSON"  # Not valid JSON

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_packages("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "Error analyzing packages" in result["issues"][0]["message"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_conflicts(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment conflicts."""
        # Setup
        mock_run.return_value = json.dumps(
            [
                {"name": "python", "version": "3.11.3", "channel": "conda-forge"},
                {"name": "numpy", "version": "1.24.3", "channel": "conda-forge"},
                {"name": "pandas", "version": "2.0.1", "channel": "conda-forge"},
            ]
        )

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_conflicts("myenv", result, False)

        # Verify
        assert result["status"] == "GOOD"
        assert not result["issues"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_conflicts_with_duplicates(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment conflicts with duplicate packages."""
        # Setup
        mock_run.return_value = json.dumps(
            [
                {"name": "python", "version": "3.11.3", "channel": "conda-forge"},
                {"name": "numpy", "version": "1.24.3", "channel": "conda-forge"},
                {"name": "numpy", "version": "1.23.5", "channel": "conda-forge"},  # Duplicate
                {"name": "pandas", "version": "2.0.1", "channel": "conda-forge"},
            ]
        )

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_conflicts("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "packages with multiple versions" in result["issues"][0]["message"]
        assert "duplicate_packages" in result["details"]
        assert len(result["details"]["duplicate_packages"]) == 1
        assert result["details"]["duplicate_packages"][0]["name"] == "numpy"
        assert len(result["details"]["duplicate_packages"][0]["versions"]) == 2

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_conflicts_command_failure(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment conflicts when command fails."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_conflicts("myenv", result, False)

        # Verify
        # This function should silently fail and not modify the result
        assert result["status"] == "GOOD"
        assert not result["issues"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_conflicts_invalid_json(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment conflicts with invalid JSON response."""
        # Setup
        mock_run.return_value = "Invalid JSON"  # Not valid JSON

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_conflicts("myenv", result, False)

        # Verify
        # This function should silently fail and not modify the result
        assert result["status"] == "GOOD"
        assert not result["issues"]

    @mock.patch("conda_forge_converter.health._calculate_directory_size")
    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_size(
        self, mock_run: mock.MagicMock, mock_calc_size: mock.MagicMock
    ) -> None:
        """Test checking environment size."""
        # Setup
        mock_run.return_value = json.dumps(
            {
                "envs": [
                    "/path/to/base",
                    "/path/to/envs/myenv",
                ]
            }
        )
        mock_calc_size.return_value = 1024 * 1024 * 1024  # 1 GB

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_size("myenv", result, False)

        # Verify
        assert result["status"] == "GOOD"
        assert not result["issues"]
        assert result["details"]["size_mb"] == 1024  # 1 GB in MB

    @mock.patch("conda_forge_converter.health._calculate_directory_size")
    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_size_large_env(
        self, mock_run: mock.MagicMock, mock_calc_size: mock.MagicMock
    ) -> None:
        """Test checking environment with a large size."""
        # Setup
        mock_run.return_value = json.dumps(
            {
                "envs": [
                    "/path/to/base",
                    "/path/to/envs/myenv",
                ]
            }
        )
        mock_calc_size.return_value = 6 * 1024 * 1024 * 1024  # 6 GB (exceeding 5 GB threshold)

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_size("myenv", result, False)

        # Verify
        assert result["status"] == "WARNING"
        assert len(result["issues"]) == 1
        assert "Environment is very large" in result["issues"][0]["message"]
        assert result["details"]["size_mb"] == 6144  # 6 GB in MB

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_size_command_failure(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment size when command fails."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_size("myenv", result, False)

        # Verify
        # This function should silently fail and not modify the result
        assert result["status"] == "GOOD"
        assert not result["issues"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_environment_size_env_not_found(self, mock_run: mock.MagicMock) -> None:
        """Test checking environment size when environment is not found."""
        # Setup
        mock_run.return_value = json.dumps(
            {
                "envs": [
                    "/path/to/base",
                    "/path/to/envs/other_env",
                ]
            }
        )

        # Create a result dictionary
        result = {"status": "GOOD", "issues": [], "details": {}}

        # Execute
        _check_environment_size("myenv", result, False)

        # Verify
        # This function should silently fail and not modify the result
        assert result["status"] == "GOOD"
        assert not result["issues"]

    def test_calculate_directory_size(self, tmp_path: Path) -> None:
        """Test calculating directory size."""
        # Setup
        # Create a temporary directory with some files
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Create some files with known sizes
        file1 = test_dir / "file1.txt"
        file1.write_text("a" * 1000)  # 1000 bytes

        file2 = test_dir / "file2.txt"
        file2.write_text("b" * 2000)  # 2000 bytes

        # Create a subdirectory with a file
        subdir = test_dir / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"
        file3.write_text("c" * 3000)  # 3000 bytes

        # Execute
        size = _calculate_directory_size(str(test_dir))

        # Verify
        assert size == 6000  # 1000 + 2000 + 3000 bytes

    def test_full_health_check(self) -> None:
        """Test the full health check function."""
        # Use direct patching of individual check functions instead of the main function
        with (
            mock.patch(
                "conda_forge_converter.health._check_environment_exists"
            ) as mock_check_exists,
            mock.patch("conda_forge_converter.health._check_python_version") as _mock_check_python,
            mock.patch(
                "conda_forge_converter.health._check_environment_packages"
            ) as _mock_check_pkgs,
            mock.patch(
                "conda_forge_converter.health._check_environment_conflicts"
            ) as _mock_check_conflicts,
            mock.patch("conda_forge_converter.health._check_environment_size") as _mock_check_size,
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

    def test_full_health_check_with_error(self) -> None:
        """Test the full health check function with an error."""
        # Use direct patching of individual check functions
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
            mock.patch("conda_forge_converter.health.logger") as mock_logger,
        ):
            # Setup the mocks to simulate an error
            def mock_error(_env_name, result, _verbose):
                result["status"] = "ERROR"
                result["issues"].append(
                    {
                        "severity": "ERROR",
                        "message": "Environment does not exist",
                        "check": "environment_exists",
                    }
                )

            mock_check_exists.side_effect = mock_error

            # Execute
            result = check_environment_health("myenv", False)

            # Verify
            assert result["status"] == "ERROR"
            assert len(result["issues"]) == 1
            assert "Environment does not exist" in result["issues"][0]["message"]

            # Verify that the other check functions were not called
            mock_check_python.assert_not_called()
            mock_check_pkgs.assert_not_called()
            mock_check_conflicts.assert_not_called()
            mock_check_size.assert_not_called()

            # Verify that the error was logged
            mock_logger.error.assert_called()

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

    @mock.patch("conda_forge_converter.health.run_command")
    def test_python_execution_failure(self, mock_run: mock.MagicMock) -> None:
        """Test running Python in the environment with failure."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Execute
        result = _test_run_python("myenv", False)

        # Verify
        assert result is False
        mock_run.assert_called_once()

    @mock.patch("conda_forge_converter.health.run_command")
    def test_python_execution_wrong_output(self, mock_run: mock.MagicMock) -> None:
        """Test running Python with unexpected output."""
        # Setup
        mock_run.return_value = "Unexpected output"  # Not containing "Hello, World!"

        # Execute
        result = _test_run_python("myenv", False)

        # Verify
        assert result is False
        mock_run.assert_called_once()

    @mock.patch("conda_forge_converter.health.run_command")
    def test_pip_test(self, mock_run: mock.MagicMock) -> None:
        """Test checking pip functionality."""
        # Setup
        mock_run.return_value = "pip 23.1.2 from /path/to/pip"

        # Execute
        result = _test_pip("myenv", False)

        # Verify
        assert result is True
        mock_run.assert_called_once()

    @mock.patch("conda_forge_converter.health.run_command")
    def test_pip_test_failure(self, mock_run: mock.MagicMock) -> None:
        """Test checking pip functionality with failure."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Execute
        result = _test_pip("myenv", False)

        # Verify
        assert result is False
        mock_run.assert_called_once()

    @mock.patch("conda_forge_converter.health.run_command")
    def test_pip_test_wrong_output(self, mock_run: mock.MagicMock) -> None:
        """Test checking pip with unexpected output."""
        # Setup
        mock_run.return_value = "Unexpected output"  # Not containing "pip"

        # Execute
        result = _test_pip("myenv", False)

        # Verify
        assert result is False
        mock_run.assert_called_once()

    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    @mock.patch("pathlib.Path.unlink")
    @mock.patch("conda_forge_converter.health.run_command")
    def test_test_imports(
        self, mock_run: mock.MagicMock, mock_unlink: mock.MagicMock, mock_open: mock.MagicMock
    ) -> None:
        """Test importing packages in the environment."""
        # Setup
        mock_run.side_effect = [
            # First call to get package list
            json.dumps(
                [
                    {"name": "numpy", "version": "1.24.3"},
                    {"name": "pandas", "version": "2.0.1"},
                ]
            ),
            # Second call to run the test script
            "SUCCESS: All imports successful",
        ]

        # Execute
        result = _test_imports("myenv", False)

        # Verify
        assert result is True
        assert mock_run.call_count == 2
        assert mock_open.called
        assert mock_unlink.called

    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    @mock.patch("pathlib.Path.unlink")
    @mock.patch("conda_forge_converter.health.run_command")
    def test_test_imports_no_packages(
        self, mock_run: mock.MagicMock, mock_unlink: mock.MagicMock, mock_open: mock.MagicMock
    ) -> None:
        """Test importing packages when no common packages are found."""
        # Setup
        mock_run.return_value = json.dumps(
            [
                {"name": "python", "version": "3.11.3"},
                {"name": "pip", "version": "23.1.2"},
            ]
        )  # No common test packages

        # Execute
        result = _test_imports("myenv", False)

        # Verify
        assert result is True
        assert mock_run.call_count == 1
        assert not mock_open.called
        assert not mock_unlink.called

    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    @mock.patch("pathlib.Path.unlink")
    @mock.patch("conda_forge_converter.health.run_command")
    def test_test_imports_command_failure(
        self, mock_run: mock.MagicMock, mock_unlink: mock.MagicMock, mock_open: mock.MagicMock
    ) -> None:
        """Test importing packages when command fails."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Execute
        result = _test_imports("myenv", False)

        # Verify
        assert result is False
        assert mock_run.call_count == 1
        assert not mock_open.called
        assert not mock_unlink.called

    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    @mock.patch("pathlib.Path.unlink")
    @mock.patch("conda_forge_converter.health.run_command")
    def test_test_imports_import_failure(
        self, mock_run: mock.MagicMock, mock_unlink: mock.MagicMock, mock_open: mock.MagicMock
    ) -> None:
        """Test importing packages when imports fail."""
        # Setup
        mock_run.side_effect = [
            # First call to get package list
            json.dumps(
                [
                    {"name": "numpy", "version": "1.24.3"},
                    {"name": "pandas", "version": "2.0.1"},
                ]
            ),
            # Second call to run the test script
            "FAILURE: Import error - No module named 'numpy'",
        ]

        # Execute
        result = _test_imports("myenv", False)

        # Verify
        assert result is False
        assert mock_run.call_count == 2
        assert mock_open.called
        assert mock_unlink.called

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_duplicate_packages(self, mock_run: mock.MagicMock) -> None:
        """Test checking for duplicate packages."""
        # Setup
        mock_run.return_value = json.dumps(
            {
                "packages": [
                    {"name": "python", "version": "3.11.3"},
                    {"name": "numpy", "version": "1.24.3"},
                    {"name": "numpy", "version": "1.23.5"},  # Duplicate
                    {"name": "pandas", "version": "2.0.1"},
                ]
            }
        )

        # Execute
        result = check_duplicate_packages("myenv")

        # Verify
        assert len(result) == 1
        assert result[0]["name"] == "numpy"
        assert len(result[0]["versions"]) == 2
        assert "1.24.3" in result[0]["versions"]
        assert "1.23.5" in result[0]["versions"]

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_duplicate_packages_no_duplicates(self, mock_run: mock.MagicMock) -> None:
        """Test checking for duplicate packages when none exist."""
        # Setup
        mock_run.return_value = json.dumps(
            {
                "packages": [
                    {"name": "python", "version": "3.11.3"},
                    {"name": "numpy", "version": "1.24.3"},
                    {"name": "pandas", "version": "2.0.1"},
                ]
            }
        )

        # Execute
        result = check_duplicate_packages("myenv")

        # Verify
        assert len(result) == 0

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_duplicate_packages_command_failure(self, mock_run: mock.MagicMock) -> None:
        """Test checking for duplicate packages when command fails."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Execute
        result = check_duplicate_packages("myenv")

        # Verify
        assert len(result) == 0

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_duplicate_packages_invalid_json(self, mock_run: mock.MagicMock) -> None:
        """Test checking for duplicate packages with invalid JSON response."""
        # Setup
        mock_run.return_value = "Invalid JSON"  # Not valid JSON

        # Execute
        result = check_duplicate_packages("myenv")

        # Verify
        assert len(result) == 0

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_package_conflicts(self, mock_run: mock.MagicMock) -> None:
        """Test checking for package conflicts."""
        # Setup
        mock_run.return_value = json.dumps(
            {
                "packages": [
                    {"name": "python", "version": "3.11.3"},
                    {"name": "numpy", "version": "1.20.0"},  # Conflict with 1.24.0
                    {"name": "pandas", "version": "2.0.1"},
                ]
            }
        )

        # Execute
        result = check_package_conflicts("myenv")

        # Verify
        assert len(result) == 2  # Both numpy and pandas have conflicts

        # Check numpy conflict
        numpy_conflict = next(item for item in result if item["name"] == "numpy")
        assert numpy_conflict["current_version"] == "1.20.0"
        assert numpy_conflict["recommended_version"] == "1.24.0"

        # Check pandas conflict
        pandas_conflict = next(item for item in result if item["name"] == "pandas")
        assert pandas_conflict["current_version"] == "2.0.1"
        assert pandas_conflict["recommended_version"] == "2.0.0"

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_package_conflicts_no_conflicts(self, mock_run: mock.MagicMock) -> None:
        """Test checking for package conflicts when none exist."""
        # Setup
        mock_run.return_value = json.dumps(
            {
                "packages": [
                    {"name": "python", "version": "3.11.3"},
                    {"name": "numpy", "version": "1.24.0"},  # Matches recommended
                    {"name": "pandas", "version": "2.0.0"},  # Matches recommended
                ]
            }
        )

        # Execute
        result = check_package_conflicts("myenv")

        # Verify
        assert len(result) == 0

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_package_conflicts_command_failure(self, mock_run: mock.MagicMock) -> None:
        """Test checking for package conflicts when command fails."""
        # Setup
        mock_run.return_value = None  # Command failed

        # Execute
        result = check_package_conflicts("myenv")

        # Verify
        assert len(result) == 0

    @mock.patch("conda_forge_converter.health.run_command")
    def test_check_package_conflicts_invalid_json(self, mock_run: mock.MagicMock) -> None:
        """Test checking for package conflicts with invalid JSON response."""
        # Setup
        mock_run.return_value = "Invalid JSON"  # Not valid JSON

        # Execute
        result = check_package_conflicts("myenv")

        # Verify
        assert len(result) == 0

    @mock.patch("tempfile.mkdtemp")
    @mock.patch("shutil.rmtree")
    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    @mock.patch("conda_forge_converter.health.run_command")
    def test_test_package_imports(
        self,
        mock_run: mock.MagicMock,
        mock_open: mock.MagicMock,
        mock_rmtree: mock.MagicMock,
        mock_mkdtemp: mock.MagicMock,
    ) -> None:
        """Test importing packages in an environment."""
        # Setup
        mock_mkdtemp.return_value = "/tmp/test_dir"
        mock_run.return_value = "All imports successful"  # No failures

        # Execute
        result = check_package_imports("myenv")

        # Verify
        assert len(result) == 0  # No failed imports
        assert mock_run.call_count == 1
        assert mock_open.called
        assert mock_rmtree.called

    @mock.patch("tempfile.mkdtemp")
    @mock.patch("shutil.rmtree")
    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    @mock.patch("conda_forge_converter.health.run_command")
    def test_test_package_imports_with_failures(
        self,
        mock_run: mock.MagicMock,
        mock_open: mock.MagicMock,
        mock_rmtree: mock.MagicMock,
        mock_mkdtemp: mock.MagicMock,
    ) -> None:
        """Test importing packages with failures."""
        # Setup
        mock_mkdtemp.return_value = "/tmp/test_dir"
        mock_run.return_value = "Failed to import: numpy, pandas"

        # Execute
        result = check_package_imports("myenv")

        # Verify
        assert len(result) == 2
        assert "numpy" in result
        assert "pandas" in result
        assert mock_run.call_count == 1
        assert mock_open.called
        assert mock_rmtree.called

    @mock.patch("tempfile.mkdtemp")
    @mock.patch("shutil.rmtree")
    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    @mock.patch("conda_forge_converter.health.run_command")
    def test_test_package_imports_command_failure(
        self,
        mock_run: mock.MagicMock,
        mock_open: mock.MagicMock,
        mock_rmtree: mock.MagicMock,
        mock_mkdtemp: mock.MagicMock,
    ) -> None:
        """Test importing packages when command fails."""
        # Setup
        mock_mkdtemp.return_value = "/tmp/test_dir"
        mock_run.return_value = None  # Command failed

        # Execute
        result = check_package_imports("myenv")

        # Verify
        assert len(result) == 1
        assert "Failed to run import tests" in result
        assert mock_run.call_count == 1
        assert mock_open.called
        assert mock_rmtree.called

    @mock.patch("tempfile.mkdtemp")
    @mock.patch("conda_forge_converter.health.logger")
    def test_test_package_imports_exception(
        self, mock_logger: mock.MagicMock, mock_mkdtemp: mock.MagicMock
    ) -> None:
        """Test importing packages when an exception occurs."""
        # Setup
        mock_mkdtemp.side_effect = Exception("Test exception")

        # Execute
        result = check_package_imports("myenv")

        # Verify
        assert len(result) == 1
        assert "Failed to run import tests" in result
        assert mock_logger.error.called
