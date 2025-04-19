"""Pytest configuration for integration tests."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest
from conda_forge_converter.utils import logger


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test that requires real conda installations",
    )
    # Ensure tests don't modify files in the workspace
    config.addinivalue_line("markers", "no_file_modifications: mark test as not modifying files")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Modify test collection to skip integration tests if conda is not available."""
    try:
        result = subprocess.run(
            ["which", "conda"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            skip_integration = pytest.mark.skip(reason="conda not available")
            for item in items:
                if "integration" in item.keywords:
                    item.add_marker(skip_integration)
    except Exception as e:
        logger.warning(f"Error checking for conda: {e!s}")
        skip_integration = pytest.mark.skip(reason="Error checking for conda")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def get_conda_info() -> dict[str, Any]:
    """Get conda information including active env and root prefix."""
    try:
        result = subprocess.run(
            ["conda", "info", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return {}


def find_conda_installation() -> Path | None:
    """Find the conda installation path."""
    try:
        conda_path = subprocess.run(
            ["which", "conda"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        if conda_path:
            return Path(conda_path).parent.parent
    except subprocess.SubprocessError:
        pass

    return None


@pytest.fixture(autouse=True)
def no_file_modifications():
    """Prevent file modifications during tests."""
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment variables to use temporary directory
        os.environ["TEMP_DIR"] = temp_dir
        os.environ["TMPDIR"] = temp_dir
        yield
        # Cleanup is handled by the context manager


@pytest.fixture(scope="session")
def conda_base_path() -> Path:
    """Fixture providing the base conda installation path."""
    conda_path = find_conda_installation()
    if not conda_path:
        pytest.skip("conda not found in PATH")
    return conda_path


@pytest.fixture(scope="session")
def anaconda_base_path(conda_info: dict[str, Any]) -> Path:
    """Fixture providing the Anaconda base installation path."""
    # Try to find Anaconda installation
    possible_paths = [
        Path("/home/arice/anaconda"),
        Path("/home/arice/anaconda3"),
        Path(conda_info.get("root_prefix", "")),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    pytest.skip("Anaconda installation not found at expected paths")


@pytest.fixture(scope="session")
def miniforge_base_path() -> Path:
    """Fixture providing the Miniforge base installation path."""
    # Try to find Miniforge installation
    possible_paths = [
        Path("/home/arice/miniforge3"),
        Path("/opt/miniforge3"),
        Path(os.path.expanduser("~/miniforge3")),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    pytest.skip("Miniforge installation not found at expected paths")


@pytest.fixture(scope="session")
def conda_info() -> dict[str, Any]:
    """Fixture providing conda information."""
    return get_conda_info()
