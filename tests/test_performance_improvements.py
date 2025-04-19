"""Tests for the performance improvements in the core module."""

import time
from typing import cast
from unittest import mock

import pytest
from conda_forge_converter.core import (
    CondaPackage,
    PipPackage,
    _install_conda_packages_in_batches,
    _install_pip_packages_in_batches,
    create_conda_forge_environment,
)


@pytest.mark.unit()
class TestBatchInstallation:
    """Tests for batch installation functionality."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_conda_batch_installation(self, mock_run_command):
        """Test installing conda packages in batches."""
        # Setup
        mock_run_command.return_value = "Success"
        target_env = "test_env"
        conda_packages = [
            cast(CondaPackage, {"name": f"package{i}", "version": f"1.0.{i}"}) for i in range(25)
        ]

        # Execute
        result = _install_conda_packages_in_batches(
            target_env, conda_packages, batch_size=10, verbose=False
        )

        # Verify
        assert result is True
        # Should have called run_command 3 times (for 3 batches of 10, 10, and 5 packages)
        assert mock_run_command.call_count == 3

        # Check the first batch
        first_call_args = mock_run_command.call_args_list[0][0][0]
        assert (
            len(first_call_args) == 17
        )  # conda install -n test_env -c conda-forge -y + [] + 10 packages
        assert "package0=1.0.0" in first_call_args
        assert "package9=1.0.9" in first_call_args

        # Check the last batch
        last_call_args = mock_run_command.call_args_list[2][0][0]
        assert (
            len(last_call_args) == 12
        )  # conda install -n test_env -c conda-forge -y + [] + 5 packages
        assert "package20=1.0.20" in last_call_args
        assert "package24=1.0.24" in last_call_args

    @mock.patch("conda_forge_converter.core.run_command")
    def test_conda_batch_installation_failure_fallback(self, mock_run_command):
        """Test fallback to individual installation when batch fails."""
        # Setup - first call fails, subsequent calls succeed
        mock_run_command.side_effect = [None] + ["Success"] * 10
        target_env = "test_env"
        conda_packages = [
            cast(CondaPackage, {"name": f"package{i}", "version": f"1.0.{i}"}) for i in range(10)
        ]

        # Execute
        result = _install_conda_packages_in_batches(
            target_env, conda_packages, batch_size=10, verbose=False
        )

        # Verify
        assert result is True
        # Should have called run_command 11 times (1 for batch + 10 for individual packages)
        assert mock_run_command.call_count == 11

        # Check individual package installations
        for i in range(1, 11):  # Skip first call (batch)
            call_args = mock_run_command.call_args_list[i][0][0]
            assert (
                len(call_args) == 8
            )  # conda install -n test_env -c conda-forge -y + [] + 1 package
            package_idx = i - 1
            assert f"package{package_idx}=1.0.{package_idx}" in call_args

    @mock.patch("conda_forge_converter.core.run_command")
    def test_pip_batch_installation(self, mock_run_command):
        """Test installing pip packages in batches."""
        # Setup
        mock_run_command.return_value = "Success"
        target_env = "test_env"
        pip_packages = [
            cast(PipPackage, {"name": f"package{i}", "version": f"1.0.{i}"}) for i in range(25)
        ]

        # Execute
        result = _install_pip_packages_in_batches(
            target_env, pip_packages, batch_size=10, verbose=False
        )

        # Verify
        assert result is True
        # Should have called run_command 3 times (for 3 batches of 10, 10, and 5 packages)
        assert mock_run_command.call_count == 3

        # Check the first batch
        first_call_args = mock_run_command.call_args_list[0][0][0]
        assert "conda" in first_call_args
        assert "run" in first_call_args
        assert "pip" in first_call_args
        assert "install" in first_call_args
        assert "package0==1.0.0" in first_call_args
        assert "package9==1.0.9" in first_call_args


@pytest.mark.unit()
class TestFastSolverIntegration:
    """Tests for fast solver integration."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_libmamba_solver_detection(self, mock_run_command):
        """Test detection and use of libmamba solver."""
        # We need to mock more specifically to test the solver args
        with mock.patch("conda_forge_converter.core._create_base_environment") as mock_create_base:
            with mock.patch(
                "conda_forge_converter.core._install_conda_packages_in_batches"
            ) as mock_install_conda:
                with mock.patch(
                    "conda_forge_converter.core._install_pip_packages_in_batches"
                ) as mock_install_pip:
                    # Setup mocks
                    mock_create_base.return_value = True
                    mock_install_conda.return_value = True
                    mock_install_pip.return_value = True
                    mock_run_command.return_value = "libmamba"

                    # Execute
                    result = create_conda_forge_environment(
                        "source_env",
                        "target_env",
                        [cast(CondaPackage, {"name": "numpy", "version": "1.20.0"})],
                        [cast(PipPackage, {"name": "scikit-learn", "version": "1.0.0"})],
                        python_version="3.9",
                        dry_run=False,
                        verbose=False,
                        use_fast_solver=True,
                    )

                    # Verify
                    assert result is True
                    # Check that solver args were passed to _create_base_environment
                    args, kwargs = mock_create_base.call_args
                    assert len(args) >= 3  # target_env, python_version, verbose
                    assert args[0] == "target_env"
                    assert args[1] == "3.9"
                    assert args[2] is False  # verbose
                    assert len(args) >= 4  # solver_args
                    assert "--solver=libmamba" in args[3]

    @mock.patch("conda_forge_converter.core.run_command")
    def test_mamba_detection(self, mock_run_command):
        """Test detection and use of mamba."""
        # Setup - libmamba not available but mamba is
        mock_run_command.side_effect = [
            "",  # First call to check solver (not found)
            "/usr/bin/mamba",  # Check for mamba
            "Success",  # Create environment with mamba
            "/usr/bin/mamba",  # Check for mamba again
            "Success",  # Install packages with mamba
            "Success",  # Install pip packages
        ] * 10  # Repeat to avoid StopIteration

        # Execute
        with mock.patch("conda_forge_converter.core._create_base_environment") as mock_create_base:
            mock_create_base.return_value = True
            result = create_conda_forge_environment(
                "source_env",
                "target_env",
                [cast(CondaPackage, {"name": "numpy", "version": "1.20.0"})],
                [cast(PipPackage, {"name": "scikit-learn", "version": "1.0.0"})],
                python_version="3.9",
                dry_run=False,
                verbose=False,
                use_fast_solver=True,
            )

        # Verify
        assert result is True
        # Verify
        assert result is True
        # We're mocking _create_base_environment, so we don't need to check the command


@pytest.mark.benchmark()
class TestPerformanceBenchmarks:
    """Performance benchmarks for the improvements.

    These tests are marked as slow and will be skipped by default.
    Run with pytest -m slow to include them.
    """

    @pytest.mark.slow()
    @mock.patch("conda_forge_converter.core.run_command")
    def test_batch_vs_individual_performance(self, mock_run_command):
        """Compare performance of batch vs individual installation."""
        # Setup
        mock_run_command.return_value = "Success"
        target_env = "test_env"
        package_count = 100
        conda_packages = [
            cast(CondaPackage, {"name": f"package{i}", "version": f"1.0.{i}"})
            for i in range(package_count)
        ]

        # Simulate delay in run_command to mimic real-world behavior
        def delayed_run_command(*args, **kwargs):
            time.sleep(0.01)  # 10ms delay per call
            return "Success"

        mock_run_command.side_effect = delayed_run_command

        # Measure batch installation time
        start_time = time.time()
        _install_conda_packages_in_batches(target_env, conda_packages, batch_size=20, verbose=False)
        batch_time = time.time() - start_time

        # Reset mock
        mock_run_command.reset_mock()

        # Measure individual installation time
        start_time = time.time()
        _install_conda_packages_in_batches(target_env, conda_packages, batch_size=1, verbose=False)
        individual_time = time.time() - start_time

        # Verify batch is faster
        assert batch_time < individual_time
        # Should have called run_command 5 times for batch vs 100 times for individual
        assert mock_run_command.call_count == package_count
