"""Unit tests for the core functionality in conda_forge_converter.core."""

import os
import json
import datetime
from unittest import mock
import pytest
from typing import Any, Dict, List, Tuple

import yaml

from conda_forge_converter.core import (
    find_environments_in_path,
    list_all_conda_environments,
    get_python_version,
    get_environment_packages,
    extract_package_specs,
    get_environment_size,
    environment_exists,
    create_conda_forge_environment,
    convert_environment,
    convert_multiple_environments,
    EnvironmentInfo,
)


@pytest.fixture
def mock_conda_environments() -> Dict[str, str]:
    """Return a mock mapping of environment names to paths."""
    return {
        "base": "/home/user/anaconda3",
        "env1": "/home/user/anaconda3/envs/env1",
        "env2": "/home/user/anaconda3/envs/env2",
        "data_science": "/home/user/anaconda3/envs/data_science",
    }


@pytest.fixture
def mock_conda_packages() -> List[Dict[str, str]]:
    """Return mock conda packages information."""
    return [
        {"name": "python", "version": "3.11.3"},
        {"name": "numpy", "version": "1.24.3"},
        {"name": "pandas", "version": "2.0.1"},
        {"name": "matplotlib", "version": "3.7.1"},
    ]


@pytest.fixture
def mock_from_history_env_yaml() -> Dict[str, Any]:
    """Return mock environment YAML from --from-history export."""
    return {
        "name": "env1",
        "channels": ["defaults"],
        "dependencies": [
            "python=3.11",
            "numpy=1.24",
            "pandas=2.0",
            {"pip": ["scikit-learn==1.2.2", "jupyterlab==4.0.0"]},
        ],
    }


@pytest.fixture
def mock_full_env_yaml() -> Dict[str, Any]:
    """Return mock environment YAML from full export."""
    return {
        "name": "env1",
        "channels": ["defaults"],
        "dependencies": [
            "python=3.11.3",
            "numpy=1.24.3",
            "pandas=2.0.1",
            "matplotlib=3.7.1",
            "scipy=1.10.1",
            "_libgcc_mutex=0.1",
            # ... many more packages
            {"pip": ["scikit-learn==1.2.2", "jupyterlab==4.0.0", "ipywidgets==8.0.6"]},
        ],
    }


class TestEnvironmentInfo:
    """Tests for the EnvironmentInfo class."""

    def test_environment_info_init(self) -> None:
        """Test initializing an EnvironmentInfo object."""
        info = EnvironmentInfo(name="env1", path="/path/to/env1")
        assert info.name == "env1"
        assert info.path == "/path/to/env1"
        assert info.python_version is None
        assert info.conda_packages == []
        assert info.pip_packages == []

    @mock.patch("conda_forge_converter.core.get_python_version")
    @mock.patch("conda_forge_converter.core.get_environment_packages")
    @mock.patch("conda_forge_converter.core.extract_package_specs")
    def test_from_environment_success(
        self,
        mock_extract: mock.MagicMock,
        mock_get_packages: mock.MagicMock,
        mock_get_python: mock.MagicMock,
    ) -> None:
        """Test creating an EnvironmentInfo from an existing environment."""
        # Setup
        mock_get_python.return_value = "3.11.3"
        mock_get_packages.return_value = (["python=3.11.3", "numpy=1.24.3"], True)
        mock_extract.return_value = (
            [{"name": "python", "version": "3.11.3"}, {"name": "numpy", "version": "1.24.3"}],
            [{"name": "scikit-learn", "version": "1.2.2"}],
        )
        
        # Execute
        info = EnvironmentInfo.from_environment("env1", "/path/to/env1")
        
        # Verify
        assert info is not None
        assert info.name == "env1"
        assert info.path == "/path/to/env1"
        assert info.python_version == "3.11.3"
        assert len(info.conda_packages) == 2
        assert len(info.pip_packages) == 1

    @mock.patch("conda_forge_converter.core.get_python_version")
    @mock.patch("conda_forge_converter.core.get_environment_packages")
    def test_from_environment_failure(
        self,
        mock_get_packages: mock.MagicMock,
        mock_get_python: mock.MagicMock,
    ) -> None:
        """Test failure when creating an EnvironmentInfo."""
        # Setup
        mock_get_python.return_value = "3.11.3"
        mock_get_packages.return_value = ([], False)  # No packages found
        
        # Execute
        info = EnvironmentInfo.from_environment("env1", "/path/to/env1")
        
        # Verify
        assert info is None


class TestFindEnvironmentsInPath:
    """Tests for find_environments_in_path function."""

    @mock.patch("os.path.exists")
    @mock.patch("os.listdir")
    @mock.patch("conda_forge_converter.core.is_conda_environment")
    def test_find_valid_environments(
        self,
        mock_is_conda_env: mock.MagicMock,
        mock_listdir: mock.MagicMock,
        mock_exists: mock.MagicMock,
    ) -> None:
        """Test finding valid conda environments in a path."""
        # Setup
        mock_exists.return_value = True
        mock_listdir.return_value = ["env1", "env2", "not_an_env"]
        mock_is_conda_env.side_effect = lambda path: "env" in os.path.basename(path)
        
        # Execute
        envs = find_environments_in_path("/path/to/envs", max_depth=2, verbose=False)
        
        # Verify
        assert len(envs) == 2
        assert "env1" in envs
        assert "env2" in envs
        assert "not_an_env" not in envs

    @mock.patch("os.path.exists")
    def test_path_does_not_exist(self, mock_exists: mock.MagicMock) -> None:
        """Test with a non-existent path."""
        # Setup
        mock_exists.return_value = False
        
        # Execute
        envs = find_environments_in_path("/path/does/not/exist", verbose=False)
        
        # Verify
        assert envs == {}


class TestListAllCondaEnvironments:
    """Tests for list_all_conda_environments function."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_registered_environments(self, mock_run: mock.MagicMock) -> None:
        """Test listing registered conda environments."""
        # Setup
        mock_output = json.dumps({
            "envs": [
                "/home/user/anaconda3",
                "/home/user/anaconda3/envs/env1",
                "/home/user/anaconda3/envs/env2",
            ]
        })
        mock_run.return_value = mock_output
        
        # Execute
        envs = list_all_conda_environments(verbose=False)
        
        # Verify
        assert len(envs) == 3
        assert envs["base"] == "/home/user/anaconda3"
        assert envs["env1"] == "/home/user/anaconda3/envs/env1"
        assert envs["env2"] == "/home/user/anaconda3/envs/env2"

    @mock.patch("conda_forge_converter.core.run_command")
    @mock.patch("conda_forge_converter.core.find_environments_in_path")
    def test_with_search_paths(
        self,
        mock_find: mock.MagicMock,
        mock_run: mock.MagicMock,
    ) -> None:
        """Test listing environments with custom search paths."""
        # Setup
        mock_output = json.dumps({
            "envs": [
                "/home/user/anaconda3",
                "/home/user/anaconda3/envs/env1",
            ]
        })
        mock_run.return_value = mock_output
        mock_find.side_effect = [
            {"env2": "/custom/path/env2"},
            {"env3": "/another/path/env3"},
        ]
        
        # Execute
        envs = list_all_conda_environments(
            search_paths=["/custom/path", "/another/path"], verbose=False
        )
        
        # Verify
        assert len(envs) == 4
        assert "env1" in envs
        assert "env2" in envs
        assert "env3" in envs


class TestGetPythonVersion:
    """Tests for get_python_version function."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_get_python_version_by_name(self, mock_run: mock.MagicMock) -> None:
        """Test getting Python version by environment name."""
        # Setup
        mock_output = json.dumps([
            {"name": "python", "version": "3.11.3", "channel": "conda-forge"}
        ])
        mock_run.return_value = mock_output
        
        # Execute
        version = get_python_version("env1", verbose=False)
        
        # Verify
        mock_run.assert_called_once_with(
            ["conda", "list", "--name", "env1", "python", "--json"], False
        )
        assert version == "3.11.3"

    @mock.patch("conda_forge_converter.core.run_command")
    def test_get_python_version_by_path(self, mock_run: mock.MagicMock) -> None:
        """Test getting Python version by environment path."""
        # Setup
        mock_output = json.dumps([
            {"name": "python", "version": "3.11.3", "channel": "conda-forge"}
        ])
        mock_run.return_value = mock_output
        
        # Execute
        version = get_python_version("env1", env_path="/path/to/env1", verbose=False)
        
        # Verify
        mock_run.assert_called_once_with(
            ["conda", "list", "--prefix", "/path/to/env1", "python", "--json"], False
        )
        assert version == "3.11.3"


class TestGetEnvironmentPackages:
    """Tests for get_environment_packages function."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_from_history_success(
        self, mock_run: mock.MagicMock, mock_from_history_env_yaml: Dict[str, Any]
    ) -> None:
        """Test getting packages from environment history."""
        # Setup
        mock_run.return_value = yaml.dump(mock_from_history_env_yaml)
        
        # Execute
        dependencies, from_history = get_environment_packages("env1", verbose=False)
        
        # Verify
        assert from_history is True
        assert len(dependencies) == 4  # 3 conda packages + 1 pip dict
        assert "python=3.11" in dependencies
        assert "numpy=1.24" in dependencies
        assert "pandas=2.0" in dependencies
        assert {"pip": ["scikit-learn==1.2.2", "jupyterlab==4.0.0"]} in dependencies

    @mock.patch("conda_forge_converter.core.run_command")
    def test_fallback_to_full_export(
        self, mock_run: mock.MagicMock, mock_full_env_yaml: Dict[str, Any]
    ) -> None:
        """Test fallback to full export when from-history fails."""
        # Setup
        # First call (with --from-history) fails
        # Second call (without --from-history) succeeds
        mock_run.side_effect = [None, yaml.dump(mock_full_env_yaml)]
        
        # Execute
        dependencies, from_history = get_environment_packages("env1", verbose=False)
        
        # Verify
        assert from_history is False
        assert len(dependencies) > 4  # Should include all dependencies


class TestExtractPackageSpecs:
    """Tests for extract_package_specs function."""

    def test_extract_conda_packages(self) -> None:
        """Test extracting conda package specifications."""
        # Setup
        dependencies = [
            "python=3.11",
            "numpy=1.24",
            "pandas",  # No version specified
            "matplotlib=3.7.1",
            "pip",  # Should be ignored
        ]
        
        # Execute
        conda_packages, pip_packages = extract_package_specs(dependencies)
        
        # Verify
        assert len(conda_packages) == 3  # Excluding "pip"
        assert conda_packages[0]["name"] == "python"
        assert conda_packages[0]["version"] == "3.11"
        assert conda_packages[2]["name"] == "pandas"
        assert conda_packages[2]["version"] is None  # No version

    def test_extract_pip_packages(self) -> None:
        """Test extracting pip package specifications."""
        # Setup
        dependencies = [
            "python=3.11",
            {"pip": [
                "scikit-learn==1.2.2",
                "jupyterlab==4.0.0",
                "ipywidgets",  # No version
            ]},
        ]
        
        # Execute
        conda_packages, pip_packages = extract_package_specs(dependencies)
        
        # Verify
        assert len(pip_packages) == 3
        assert pip_packages[0]["name"] == "scikit-learn"
        assert pip_packages[0]["version"] == "1.2.2"
        assert pip_packages[2]["name"] == "ipywidgets"
        assert pip_packages[2]["version"] is None


class TestEnvironmentExists:
    """Tests for environment_exists function."""

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    def test_environment_exists(self, mock_list: mock.MagicMock) -> None:
        """Test checking if an environment exists."""
        # Setup
        mock_list.return_value = {
            "base": "/home/user/anaconda3",
            "env1": "/home/user/anaconda3/envs/env1",
        }
        
        # Execute & Verify
        assert environment_exists("env1") is True
        assert environment_exists("nonexistent_env") is False


class TestGetEnvironmentSize:
    """Tests for get_environment_size function."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_calculate_environment_size(
        self, mock_run: mock.MagicMock, mock_full_env_yaml: Dict[str, Any]
    ) -> None:
        """Test calculating environment size based on package count."""
        # Setup
        # Make sure we have at least 5 conda packages and 3 pip packages for testing
        dependencies = mock_full_env_yaml["dependencies"]
        pip_dict = next((d for d in dependencies if isinstance(d, dict) and "pip" in d), None)
        assert pip_dict is not None
        assert len(pip_dict["pip"]) >= 3
        
        mock_run.return_value = yaml.dump(mock_full_env_yaml)
        
        # Execute
        size_mb = get_environment_size("env1", verbose=False)
        
        # Verify - should be (conda_count + pip_count) * 50
        conda_count = sum(1 for d in dependencies if isinstance(d, str))
        pip_count = len(pip_dict["pip"])
        expected_size = (conda_count + pip_count) * 50
        
        assert size_mb == expected_size


class TestCreateCondaForgeEnvironment:
    """Tests for create_conda_forge_environment function."""

    def test_dry_run(self) -> None:
        """Test dry run mode."""
        # Setup
        conda_packages = [
            {"name": "numpy", "version": "1.24.3"},
            {"name": "pandas", "version": "2.0.1"},
        ]
        pip_packages = [
            {"name": "scikit-learn", "version": "1.2.2"},
        ]
        
        # Execute
        result = create_conda_forge_environment(
            "source_env", "target_env", conda_packages, pip_packages,
            python_version="3.11.3", dry_run=True, verbose=False
        )
        
        # Verify
        assert result is True  # Dry run always succeeds

    @mock.patch("conda_forge_converter.core.run_command")
    def test_successful_creation(self, mock_run: mock.MagicMock) -> None:
        """Test successful environment creation."""
        # Setup
        conda_packages = [
            {"name": "numpy", "version": "1.24.3"},
            {"name": "pandas", "version": "2.0.1"},
        ]
        pip_packages = [
            {"name": "scikit-learn", "version": "1.2.2"},
        ]
        
        # All commands succeed
        mock_run.return_value = True
        
        # Execute
        result = create_conda_forge_environment(
            "source_env", "target_env", conda_packages, pip_packages,
            python_version="3.11.3", dry_run=False, verbose=False
        )
        
        # Verify
        assert result is True
        assert mock_run.call_count == 3  # create env, install conda pkgs, install pip pkgs

    @mock.patch("conda_forge_converter.core.run_command")
    def test_creation_failure(self, mock_run: mock.MagicMock) -> None:
        """Test environment creation failure."""
        # Setup
        conda_packages = [
            {"name": "numpy", "version": "1.24.3"},
        ]
        
        # First call succeeds (create env), second call fails (install packages)
        mock_run.side_effect = [True, None]
        
        # Execute
        result = create_conda_forge_environment(
            "source_env", "target_env", conda_packages, [],
            python_version="3.11.3", dry_run=False, verbose=False
        )
        
        # Verify
        assert result is False


class TestConvertEnvironment:
    """Tests for convert_environment function."""

    @mock.patch("conda_forge_converter.core.environment_exists")
    @mock.patch("conda_forge_converter.core.EnvironmentInfo.from_environment")
    @mock.patch("conda_forge_converter.core.create_conda_forge_environment")
    def test_successful_conversion(
        self,
        mock_create: mock.MagicMock,
        mock_from_env: mock.MagicMock,
        mock_exists: mock.MagicMock,
    ) -> None:
        """Test successful environment conversion."""
        # Setup
        mock_exists.return_value = False  # Target env doesn't exist
        env_info = EnvironmentInfo(
            name="source_env",
            path="/path/to/source_env",
            python_version="3.11.3",
            conda_packages=[{"name": "numpy", "version": "1.24.3"}],
            pip_packages=[{"name": "scikit-learn", "version": "1.2.2"}]
        )
        mock_from_env.return_value = env_info
        mock_create.return_value = True
        
        # Execute
        result = convert_environment("source_env", "target_env", verbose=False)
        
        # Verify
        assert result is True
        mock_create.assert_called_once_with(
            "source_env", "target_env",
            env_info.conda_packages, env_info.pip_packages,
            env_info.python_version, False, False
        )

    @mock.patch("conda_forge_converter.core.environment_exists")
    def test_target_already_exists(self, mock_exists: mock.MagicMock) -> None:
        """Test when target environment already exists."""
        # Setup
        mock_exists.return_value = True  # Target env already exists
        
        # Execute
        result = convert_environment("source_env", "target_env", verbose=False)
        
        # Verify
        assert result is False

    @mock.patch("conda_forge_converter.core.environment_exists")
    @mock.patch("conda_forge_converter.core.EnvironmentInfo.from_environment")
    def test_environment_info_failure(
        self,
        mock_from_env: mock.MagicMock,
        mock_exists: mock.MagicMock,
    ) -> None:
        """Test when environment info can't be obtained."""
        # Setup
        mock_exists.return_value = False  # Target env doesn't exist
        mock_from_env.return_value = None  # Can't get environment info
        
        # Execute
        result = convert_environment("source_env", "target_env", verbose=False)
        
        # Verify
        assert result is False


class TestConvertMultipleEnvironments:
    """Tests for convert_multiple_environments function."""

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    def test_no_environments_found(self, mock_list: mock.MagicMock) -> None:
        """Test when no environments are found."""
        # Setup
        mock_list.return_value = {}  # No environments
        
        # Execute
        result = convert_multiple_environments(verbose=False)
        
        # Verify
        assert result is False

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    def test_pattern_filtering(
        self,
        mock_list: mock.MagicMock,
        mock_conda_environments: Dict[str, str],
    ) -> None:
        """Test filtering environments by pattern."""
        # Setup
        mock_list.return_value = mock_conda_environments
        
        # Using a pattern fixture to avoid actually running conversions
        with mock.patch("conda_forge_converter.core.process_environment") as _:
            # Execute - should only find data_science environment
            result = convert_multiple_environments(
                env_pattern="data*", dry_run=True, verbose=False
            )
            
            # No environments to convert since we mocked process_environment
            assert result is False

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    def test_with_exclusions(
        self,
        mock_list: mock.MagicMock,
        mock_conda_environments: Dict[str, str],
    ) -> None:
        """Test excluding specific environments."""
        # Setup
        mock_list.return_value = mock_conda_environments
        
        # Using a fixture to avoid actually running conversions
        with mock.patch("conda_forge_converter.core.process_environment") as _:
            # Execute - should exclude env1
            result = convert_multiple_environments(
                exclude="env1,base", dry_run=True, verbose=False
            )
            
            # No environments to convert since we mocked process_environment
            assert result is False

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    @mock.patch("conda_forge_converter.core.get_environment_size")
    @mock.patch("conda_forge_converter.core.check_disk_space")
    def test_disk_space_check(
        self,
        mock_check_space: mock.MagicMock,
        mock_get_size: mock.MagicMock,
        mock_list: mock.MagicMock,
        mock_conda_environments: Dict[str, str],
    ) -> None:
        """Test disk space check before conversion."""
        # Setup
        mock_list.return_value = mock_conda_environments
        mock_get_size.return_value = 500  # Each env is 500MB
        mock_check_space.return_value = False  # Not enough space
        
        # Mock input function to simulate user saying "no" to continue anyway
        with mock.patch("builtins.input", return_value="n"):
            # Execute
            result = convert_multiple_environments(verbose=False)
            
            # Verify
            assert result is False

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    @mock.patch("conda_forge_converter.core.get_environment_packages")
    @mock.patch("conda_forge_converter.core.extract_package_specs")
    @mock.patch("conda_forge_converter.core.create_conda_forge_environment")
    @mock.patch("conda_forge_converter.core.environment_exists")
    def test_parallel_conversion(
        self,
        mock_exists: mock.MagicMock,
        mock_create: mock.MagicMock,
        mock_extract: mock.MagicMock,
        mock_get_packages: mock.MagicMock,
        mock_list: mock.MagicMock,
        mock_conda_environments: Dict[str, str],
    ) -> None:
        """Test parallel conversion of environments."""
        # Setup
        mock_list.return_value = mock_conda_environments
        mock_exists.return_value = False  # Target environments don't exist
        mock_get_packages.return_value = (["python=3.11"], True)
        mock_extract.return_value = ([{"name": "python", "version": "3.11"}], [])
        mock_create.return_value = True
        
        # Execute
        with mock.patch("conda_forge_converter.core.check_disk_space", return_value=True):
            with mock.patch("conda_forge_converter.core.get_environment_size", return_value=100):
                result = convert_multiple_environments(max_parallel=2, verbose=False)
                
                # Verify
                assert result is True
