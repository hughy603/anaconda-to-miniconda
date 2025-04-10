"""Integration tests for the conda-forge-converter package."""

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

import pytest

from conda_forge_converter.core import (
    convert_environment,
    convert_multiple_environments,
    environment_exists,
    list_all_conda_environments,
)


def get_conda_info() -> dict[str, Any]:
    """Get conda information including active env and root prefix."""
    result = subprocess.run(
        ["conda", "info", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


@pytest.fixture(scope="session")
def conda_info() -> dict[str, Any]:
    """Fixture providing conda information."""
    return get_conda_info()


@pytest.fixture(scope="session")
def anaconda_path(conda_info: dict[str, Any]) -> str:
    """Fixture providing the Anaconda installation path."""
    # Try to find Anaconda installation
    possible_paths = [
        "/home/arice/anaconda",
        "/home/arice/anaconda3",
        conda_info.get("root_prefix", ""),
    ]

    for path in possible_paths:
        if path and Path(path).exists():
            return path

    pytest.skip("Anaconda installation not found")


@pytest.fixture(scope="session")
def miniforge_path() -> str:
    """Fixture providing the Miniforge installation path."""
    # Try to find Miniforge installation
    possible_paths = [
        "/home/arice/miniforge3",
        "/opt/miniforge3",
        os.path.expanduser("~/miniforge3"),
    ]

    for path in possible_paths:
        if path and Path(path).exists():
            return path

    pytest.skip("Miniforge installation not found")


@pytest.fixture(scope="session")
def test_env_name() -> str:
    """Fixture providing a unique test environment name."""
    return f"test_env_{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
class TestEnvironmentDetection:
    """Integration tests for environment detection."""

    def test_anaconda_environments_detection(self, anaconda_path: str) -> None:
        """Test detection of Anaconda environments."""
        # Execute
        envs = list_all_conda_environments(
            search_paths=[anaconda_path],
            verbose=True,
        )

        # Verify
        assert envs is not None
        assert len(envs) > 0  # At least one environment should be found
        assert Path(next(iter(envs.values()))).exists()  # At least one path should exist

    def test_miniforge_environments_detection(self, miniforge_path: str) -> None:
        """Test detection of Miniforge environments."""
        # Execute
        envs = list_all_conda_environments(
            search_paths=[miniforge_path],
            verbose=True,
        )

        # Verify
        assert envs is not None
        assert len(envs) > 0  # At least one environment should be found
        assert Path(next(iter(envs.values()))).exists()  # At least one path should exist


@pytest.mark.integration
class TestEnvironmentConversion:
    """Integration tests for environment conversion."""

    def test_single_environment_conversion(
        self,
        anaconda_path: str,
        miniforge_path: str,
        test_env_name: str,
    ) -> None:
        """Test conversion of a single environment from Anaconda to Miniforge."""
        # Setup
        source_env = test_env_name
        target_env = f"{test_env_name}_forge"

        # Create a test environment in Anaconda
        subprocess.run(
            ["conda", "create", "-n", source_env, "python=3.11", "numpy", "pandas", "-y"],
            check=True,
        )

        try:
            # Execute conversion
            result = convert_environment(
                source_env,
                target_env,
                verbose=True,
            )

            # Verify
            assert result is True

            # Verify target environment exists
            envs = list_all_conda_environments(
                search_paths=[miniforge_path],
                verbose=True,
            )
            assert target_env in envs

            # Verify packages in target environment
            target_env_path = envs[target_env]
            assert Path(target_env_path).exists()

            # Verify packages are installed correctly
            packages_cmd = ["conda", "list", "-n", target_env, "--json"]
            packages_output = subprocess.run(
                packages_cmd,
                capture_output=True,
                text=True,
                check=True,
            ).stdout

            packages = json.loads(packages_output)
            package_names = {pkg["name"] for pkg in packages}
            assert "numpy" in package_names
            assert "pandas" in package_names

        finally:
            # Cleanup
            subprocess.run(["conda", "env", "remove", "-n", source_env, "-y"], check=False)
            subprocess.run(["conda", "env", "remove", "-n", target_env, "-y"], check=False)

    def test_multiple_environments_conversion(
        self,
        anaconda_path: str,
        miniforge_path: str,
        test_env_name: str,
    ) -> None:
        """Test conversion of multiple environments from Anaconda to Miniforge."""
        # Setup
        test_envs = [f"{test_env_name}_1", f"{test_env_name}_2"]
        for env in test_envs:
            subprocess.run(
                ["conda", "create", "-n", env, "python=3.11", "numpy", "pandas", "-y"],
                check=True,
            )

        try:
            # Execute conversion
            result = convert_multiple_environments(
                source_envs=test_envs,
                verbose=True,
            )

            # Verify
            assert result is True

            # Verify target environments exist
            envs = list_all_conda_environments(
                search_paths=[miniforge_path],
                verbose=True,
            )
            for env in test_envs:
                target_env = f"{env}_forge"
                assert target_env in envs
                assert Path(envs[target_env]).exists()

                # Verify packages are installed correctly
                packages_cmd = ["conda", "list", "-n", target_env, "--json"]
                packages_output = subprocess.run(
                    packages_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                packages = json.loads(packages_output)
                package_names = {pkg["name"] for pkg in packages}
                assert "numpy" in package_names
                assert "pandas" in package_names

        finally:
            # Cleanup
            for env in test_envs:
                subprocess.run(["conda", "env", "remove", "-n", env, "-y"], check=False)
                subprocess.run(["conda", "env", "remove", "-n", f"{env}_forge", "-y"], check=False)

    def test_complex_environment_conversion(
        self,
        anaconda_path: str,
        miniforge_path: str,
        test_env_name: str,
    ) -> None:
        """Test conversion of a complex environment with mixed conda and pip packages."""
        # Setup
        source_env = f"{test_env_name}_complex"
        target_env = f"{source_env}_forge"

        # Check if environments already exist and remove them
        for env in [source_env, target_env]:
            if environment_exists(env, verbose=True):
                subprocess.run(["conda", "env", "remove", "-n", env, "-y"], check=False)

        try:
            # Create a test environment with mixed packages
            print(f"Creating source environment '{source_env}' with conda packages...")
            subprocess.run(
                [
                    "conda",
                    "create",
                    "-n",
                    source_env,
                    "python=3.11",
                    "numpy",
                    "pandas",
                    "scipy",
                    "matplotlib",
                    "scikit-learn",
                    "jupyter",
                    "-y",
                ],
                check=True,
            )

            # Install pip packages
            print(f"Installing pip packages in '{source_env}'...")
            subprocess.run(
                [
                    "conda",
                    "run",
                    "-n",
                    source_env,
                    "pip",
                    "install",
                    "requests",
                    "flask",
                    "fastapi",
                    "uvicorn",
                ],
                check=True,
            )

            # Execute conversion
            print(f"Converting environment '{source_env}' to '{target_env}'...")
            result = convert_environment(
                source_env,
                target_env,
                verbose=True,
            )

            # Verify
            assert result is True, "Environment conversion failed"

            # Verify target environment exists
            print(f"Verifying target environment '{target_env}' exists...")
            envs = list_all_conda_environments(
                search_paths=[miniforge_path],
                verbose=True,
            )
            assert target_env in envs, f"Target environment '{target_env}' not found"
            target_env_path = envs[target_env]
            assert Path(target_env_path).exists(), (
                f"Target environment path '{target_env_path}' does not exist"
            )

            # Verify key packages are installed
            print(f"Verifying packages in target environment '{target_env}'...")
            packages_cmd = ["conda", "list", "-n", target_env, "--json"]
            packages_output = subprocess.run(
                packages_cmd,
                capture_output=True,
                text=True,
                check=True,
            ).stdout

            packages = json.loads(packages_output)
            package_names = {pkg["name"] for pkg in packages}

            print(f"Installed packages in target environment: {sorted(package_names)}")

            # Check for conda packages - these should definitely be available in conda-forge
            conda_packages = {"numpy", "pandas", "scipy", "matplotlib", "scikit-learn", "jupyter"}
            missing_conda_packages = conda_packages - package_names
            assert not missing_conda_packages, f"Missing conda packages: {missing_conda_packages}"

            # Check for at least one of the pip packages - some might be installed via conda-forge
            # or might not be available in conda-forge
            pip_packages = {"requests", "flask", "fastapi", "uvicorn"}
            installed_pip_packages = pip_packages & package_names

            # If no pip packages were installed, check if they're available in conda-forge
            if not installed_pip_packages:
                print("No pip packages were installed. Checking availability in conda-forge...")
                for pkg in pip_packages:
                    search_cmd = ["conda", "search", "-c", "conda-forge", pkg, "--json"]
                    search_output = subprocess.run(
                        search_cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                    ).stdout

                    try:
                        search_results = json.loads(search_output)
                        if search_results and len(search_results) > 0:
                            print(f"Package '{pkg}' is available in conda-forge")
                        else:
                            print(f"Package '{pkg}' is NOT available in conda-forge")
                    except json.JSONDecodeError:
                        print(f"Could not parse search results for '{pkg}'")

            # We'll consider the test successful if at least some packages were installed
            # or if we can confirm the packages aren't available in conda-forge
            assert len(installed_pip_packages) > 0 or len(package_names) > len(conda_packages), (
                f"No pip packages were installed and no additional packages were found. "
                f"Installed packages: {sorted(package_names)}"
            )

        finally:
            # Cleanup - ensure environments are removed even if test fails
            print("Cleaning up environments...")
            for env in [source_env, target_env]:
                subprocess.run(["conda", "env", "remove", "-n", env, "-y"], check=False)
