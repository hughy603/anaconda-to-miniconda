"""Tests for the reporting module."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from conda_forge_converter.reporting import (
    _calculate_changes,
    _collect_environment_info,
    generate_conversion_report,
    generate_summary_report,
)


class TestReporting:
    """Tests for the reporting functionality."""

    def test_calculate_changes(self) -> None:
        """Test calculating changes between environments."""
        # Setup sample environment info
        source_info = {
            "name": "source_env",
            "python_version": "3.9.5",
            "conda_packages": [
                {"name": "numpy", "version": "1.20.3", "build": "py39hd249d9e_0"},
                {"name": "pandas", "version": "1.3.0", "build": "py39hc955d3c_0"},
                {"name": "matplotlib", "version": "3.4.2", "build": "py39hc955d3c_0"},
                {"name": "removed_pkg", "version": "1.0.0", "build": "py39hc955d3c_0"},
            ],
            "pip_packages": [
                {"name": "scikit-learn", "version": "0.24.2", "build": ""},
            ],
            "total_packages": 5,
            "channels": {
                "anaconda": 3,
                "defaults": 1,
                "pypi": 1,
            },
        }

        target_info = {
            "name": "target_env",
            "python_version": "3.9.5",
            "conda_packages": [
                {"name": "numpy", "version": "1.20.3", "build": "py39h9dfe65a_0"},  # build changed
                {
                    "name": "pandas",
                    "version": "1.3.1",
                    "build": "py39hc955d3c_0",
                },  # version changed
                {"name": "matplotlib", "version": "3.4.2", "build": "py39hc955d3c_0"},  # unchanged
                {"name": "added_pkg", "version": "2.0.0", "build": "py39hc955d3c_0"},  # new package
            ],
            "pip_packages": [
                {"name": "scikit-learn", "version": "0.24.2", "build": ""},
            ],
            "total_packages": 5,
            "channels": {
                "conda-forge": 4,
                "pypi": 1,
            },
        }

        # Execute
        changes = _calculate_changes(source_info, target_info)

        # Verify
        assert changes["python_version"]["changed"] is False
        assert len(changes["changed_packages"]) == 2  # numpy and pandas
        assert len(changes["added_packages"]) == 1  # added_pkg
        assert len(changes["removed_packages"]) == 1  # removed_pkg

        # Check channel changes
        assert changes["channel_changes"]["anaconda"]["source"] == 3
        assert changes["channel_changes"]["anaconda"]["target"] == 0
        assert changes["channel_changes"]["conda-forge"]["source"] == 0
        assert changes["channel_changes"]["conda-forge"]["target"] == 4

    @mock.patch("conda_forge_converter.reporting.run_command")
    def test_collect_environment_info(self, mock_run: mock.MagicMock) -> None:
        """Test collecting environment information."""
        # Setup
        env_list_output = '{"envs": ["/path/to/base", "/path/to/envs/myenv"]}'
        pkg_list_output = """[
            {"name": "python", "version": "3.11.3", "build": "py310h4646af0_0", "channel": "conda-forge"},
            {"name": "numpy", "version": "1.24.3", "build": "py311h64a7726_0", "channel": "conda-forge"},
            {"name": "pandas", "version": "2.0.1", "build": "py311hf62ec03_0", "channel": "conda-forge"},
            {"name": "scikit-learn", "version": "1.2.2", "build": "py311", "channel": "pypi"}
        ]"""

        mock_run.side_effect = [env_list_output, pkg_list_output]

        # Execute
        env_info = _collect_environment_info("myenv", False)

        # Verify
        assert env_info["name"] == "myenv"
        assert env_info["python_version"] == "3.11.3"
        assert len(env_info["conda_packages"]) == 3
        assert len(env_info["pip_packages"]) == 1
        assert env_info["total_packages"] == 4
        assert env_info["channels"]["conda-forge"] == 3
        assert env_info["channels"]["pypi"] == 1

    @mock.patch("conda_forge_converter.reporting._collect_environment_info")
    def test_generate_conversion_report(self, mock_collect: mock.MagicMock) -> None:
        """Test generating a conversion report."""
        # Setup
        source_info = {
            "name": "source_env",
            "python_version": "3.11.3",
            "conda_packages": [{"name": "numpy", "version": "1.24.3", "build": ""}],
            "pip_packages": [],
            "total_packages": 1,
            "channels": {"conda-forge": 1},
        }

        target_info = {
            "name": "target_env",
            "python_version": "3.11.3",
            "conda_packages": [{"name": "numpy", "version": "1.24.3", "build": ""}],
            "pip_packages": [],
            "total_packages": 1,
            "channels": {"conda-forge": 1},
        }

        mock_collect.side_effect = [source_info, target_info]

        # Execute
        report = generate_conversion_report("source_env", "target_env", True, verbose=False)

        # Verify
        assert report.source_env == "source_env"
        assert report.target_env == "target_env"
        assert report.success is True
        assert report.start_time is not None
        assert report.end_time is not None
        assert report.metadata.get("source_info") == source_info
        assert report.metadata.get("target_info") == target_info
        assert "changes" in report.metadata

    def test_generate_summary_report(self) -> None:
        """Test generating a summary report."""
        # Setup
        conversion_results = {
            "success": [("env1", "env1_forge"), ("env2", "env2_forge")],
            "failed": [("env3", "Failed to convert")],
            "skipped": [("env4", "Target already exists")],
        }

        # Execute
        summary = generate_summary_report(conversion_results)

        # Verify
        assert summary["total_environments"] == 4
        assert summary["successful"] == 2
        assert summary["failed"] == 1
        assert summary["skipped"] == 1
        assert summary["success_rate"] == 66.7  # 2/3 * 100 rounded to 1 decimal
        assert summary["details"] == conversion_results

    @mock.patch("conda_forge_converter.reporting._write_report")
    def test_report_file_output(self, mock_write: mock.MagicMock) -> None:
        """Test writing report to file."""
        # Setup
        with TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "report.json"

            @mock.patch("conda_forge_converter.reporting._collect_environment_info")
            def test_with_output_file(mock_collect: mock.MagicMock) -> None:
                source_info = {"name": "source_env", "python_version": "3.11.3"}
                target_info = {"name": "target_env", "python_version": "3.11.3"}
                mock_collect.side_effect = [source_info, target_info]

                # Execute
                generate_conversion_report(
                    "source_env", "target_env", True, output_file=str(output_file), verbose=False
                )

            # Run the test
            test_with_output_file()

            # Verify
            mock_write.assert_called_once()
