"""Tests for the incremental update module."""

from unittest import mock

from conda_forge_converter.incremental import (
    _update_package,
    check_for_updates,
    detect_drift,
    get_environment_packages,
    update_conda_forge_environment,
)


class TestIncrementalUpdates:
    """Tests for the incremental update functionality."""

    @mock.patch("conda_forge_converter.incremental.run_command")
    def test_get_environment_packages(self, mock_run: mock.MagicMock) -> None:
        """Test getting packages from an environment."""
        # Setup
        mock_run.return_value = """[
            {"name": "python", "version": "3.11.3", "channel": "conda-forge"},
            {"name": "numpy", "version": "1.24.3", "channel": "conda-forge"},
            {"name": "pandas", "version": "2.0.1", "channel": "conda-forge"},
            {"name": "scikit-learn", "version": "1.2.2", "channel": "pypi"}
        ]"""

        # Execute
        packages = get_environment_packages("myenv", False)

        # Verify
        assert len(packages) == 3  # Should exclude pip package
        assert packages["python"] == "3.11.3"
        assert packages["numpy"] == "1.24.3"
        assert packages["pandas"] == "2.0.1"
        assert "scikit-learn" not in packages

    @mock.patch("conda_forge_converter.incremental.environment_exists")
    @mock.patch("conda_forge_converter.incremental.get_environment_packages")
    def test_check_for_updates(
        self, mock_get_packages: mock.MagicMock, mock_exists: mock.MagicMock
    ) -> None:
        """Test checking for updates between environments."""
        # Setup
        mock_exists.return_value = True

        source_packages = {
            "python": "3.11.3",
            "numpy": "1.24.3",
            "pandas": "2.0.1",
            "matplotlib": "3.7.1",
            "only_in_source": "1.0.0",
        }

        target_packages = {
            "python": "3.11.3",  # Same version
            "numpy": "1.24.2",  # Older version
            "pandas": "2.0.1",  # Same version
            "only_in_target": "2.0.0",  # Only in target
        }

        mock_get_packages.side_effect = [source_packages, target_packages]

        # Execute
        outdated, source_only = check_for_updates("myenv_forge", False)

        # Verify
        assert len(outdated) == 1
        assert outdated[0]["name"] == "numpy"
        assert outdated[0]["source_version"] == "1.24.3"
        assert outdated[0]["target_version"] == "1.24.2"

        assert len(source_only) == 2
        assert {"name": "matplotlib", "version": "3.7.1"} in source_only
        assert {"name": "only_in_source", "version": "1.0.0"} in source_only

    @mock.patch("conda_forge_converter.incremental.environment_exists")
    def test_check_for_updates_missing_env(self, mock_exists: mock.MagicMock) -> None:
        """Test checking for updates with missing environments."""
        # Setup
        mock_exists.return_value = False

        # Execute
        outdated, source_only = check_for_updates("myenv_forge", False)

        # Verify
        assert len(outdated) == 0
        assert len(source_only) == 0

    @mock.patch("conda_forge_converter.incremental.run_command")
    def test_update_package(self, mock_run: mock.MagicMock) -> None:
        """Test updating a package in an environment."""
        # Setup
        mock_run.return_value = "Success"

        # Execute
        result = _update_package("myenv_forge", "numpy", "1.24.3", False)

        # Verify
        assert result is True
        mock_run.assert_called_once()
        # Check that the command includes the package name and version
        assert "numpy=1.24.3" in mock_run.call_args[0][0]

    @mock.patch("conda_forge_converter.incremental.check_for_updates")
    @mock.patch("conda_forge_converter.incremental._update_package")
    def test_update_conda_forge_environment(
        self, mock_update: mock.MagicMock, mock_check: mock.MagicMock
    ) -> None:
        """Test updating a conda-forge environment."""
        # Setup
        outdated_packages = [
            {"name": "numpy", "source_version": "1.24.3", "target_version": "1.24.2"},
            {"name": "pandas", "source_version": "2.0.1", "target_version": "1.5.3"},
        ]

        source_only_packages = [
            {"name": "matplotlib", "version": "3.7.1"},
        ]

        mock_check.return_value = (outdated_packages, source_only_packages)
        mock_update.return_value = True

        # Execute - update all outdated packages
        result = update_conda_forge_environment(
            "myenv_forge", update_all=True, add_missing=False, verbose=False
        )

        # Verify
        assert len(result["outdated_packages"]) == 2
        assert len(result["updated_packages"]) == 2
        assert "numpy" in result["updated_packages"]
        assert "pandas" in result["updated_packages"]
        assert not result["added_packages"]
        assert not result["failed_updates"]

        # Check that _update_package was called twice
        assert mock_update.call_count == 2

    @mock.patch("conda_forge_converter.incremental.check_for_updates")
    @mock.patch("conda_forge_converter.incremental._update_package")
    def test_update_specific_packages(
        self, mock_update: mock.MagicMock, mock_check: mock.MagicMock
    ) -> None:
        """Test updating specific packages."""
        # Setup
        outdated_packages = [
            {"name": "numpy", "source_version": "1.24.3", "target_version": "1.24.2"},
            {"name": "pandas", "source_version": "2.0.1", "target_version": "1.5.3"},
        ]

        source_only_packages = [
            {"name": "matplotlib", "version": "3.7.1"},
        ]

        mock_check.return_value = (outdated_packages, source_only_packages)
        mock_update.return_value = True

        # Execute - update specific package
        result = update_conda_forge_environment(
            "myenv_forge",
            update_all=False,
            add_missing=False,
            specific_packages=["numpy"],
            verbose=False,
        )

        # Verify
        assert len(result["updated_packages"]) == 1
        assert "numpy" in result["updated_packages"]
        assert "pandas" not in result["updated_packages"]

        # Check that _update_package was called once
        assert mock_update.call_count == 1

    @mock.patch("conda_forge_converter.incremental.check_for_updates")
    @mock.patch("conda_forge_converter.incremental._update_package")
    def test_add_missing_packages(
        self, mock_update: mock.MagicMock, mock_check: mock.MagicMock
    ) -> None:
        """Test adding missing packages."""
        # Setup
        outdated_packages: list[dict[str, str]] = []

        source_only_packages = [
            {"name": "matplotlib", "version": "3.7.1"},
            {"name": "seaborn", "version": "0.12.2"},
        ]

        mock_check.return_value = (outdated_packages, source_only_packages)
        mock_update.return_value = True

        # Execute - add missing packages
        result = update_conda_forge_environment(
            "myenv_forge", update_all=False, add_missing=True, verbose=False
        )

        # Verify
        assert len(result["added_packages"]) == 2
        assert "matplotlib" in result["added_packages"]
        assert "seaborn" in result["added_packages"]

        # Check that _update_package was called twice (for adding packages)
        assert mock_update.call_count == 2

    @mock.patch("conda_forge_converter.incremental.compare_environments")
    def test_detect_drift(self, mock_compare: mock.MagicMock) -> None:
        """Test detecting drift between environments."""
        # Setup
        compare_result = {
            "source_environment": "myenv",
            "target_environment": "myenv_forge",
            "source_package_count": 10,
            "target_package_count": 8,
            "source_only": [{"name": "pkg1", "version": "1.0"}],
            "target_only": [],
            "different_versions": [
                {"name": "pkg2", "source_version": "2.0", "target_version": "1.9"}
            ],
            "same_versions": [{"name": "pkg3", "version": "3.0"}],
            "environment_similarity": 80.0,
        }

        mock_compare.return_value = compare_result

        # Execute
        result = detect_drift("myenv_forge", False)

        # Verify
        assert result == compare_result
        mock_compare.assert_called_once()
