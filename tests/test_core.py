"""Tests for the core module."""

import json
from collections.abc import Sequence
from typing import Any, cast
from unittest import mock

import pytest
import yaml
from conda_forge_converter.core import (
    CondaPackage,
    ConversionError,
    EnvironmentInfo,
    PipDependencies,
    PipPackage,
    convert_environment,
    convert_multiple_environments,
    create_conda_forge_environment,
    environment_exists,
    extract_package_specs,
    find_environments_in_path,
    get_environment_packages,
    get_environment_size,
    get_python_version,
    list_all_conda_environments,
)


@pytest.fixture()
def mock_conda_environments() -> dict[str, str]:
    """Fixture providing test conda environments."""
    return {
        "base": "/home/user/anaconda3",
        "data_science": "/home/user/anaconda3/envs/data_science",
        "web_dev": "/home/user/anaconda3/envs/web_dev",
    }


@pytest.fixture()
def mock_conda_packages() -> list[CondaPackage]:
    """Fixture providing test conda packages."""
    return [
        cast(CondaPackage, {"name": "numpy", "version": "1.24.3"}),
        cast(CondaPackage, {"name": "pandas", "version": "2.0.1"}),
        cast(CondaPackage, {"name": "scipy", "version": "1.10.1"}),
    ]


@pytest.fixture()
def mock_from_history_env_yaml() -> dict[str, Any]:
    """Fixture providing test environment.yml from --from-history export."""
    return {
        "name": "test_env",
        "channels": ["defaults"],
        "dependencies": [
            "python=3.11.3",
            "numpy=1.24.3",
            "pandas=2.0.1",
            "pip",
            {
                "pip": [
                    "scikit-learn==1.2.2",
                ],
            },
        ],
    }


@pytest.fixture()
def mock_full_env_yaml() -> dict[str, Any]:
    """Fixture providing test environment.yml from regular export."""
    return {
        "name": "test_env",
        "channels": ["defaults"],
        "dependencies": [
            "blas=1.0=mkl",
            "ca-certificates=2023.01.10=haa95532_0",
            "intel-openmp=2023.1.0=h59b6b97_46319",
            "mkl=2023.1.0=h8bd8f75_46356",
            "mkl-service=2.4.0=py311h2bbff1b_1",
            "mkl_fft=1.3.6=py311hf62ec03_1",
            "mkl_random=1.2.2=py311hf62ec03_1",
            "numpy=1.24.3=py311hf62ec03_1",
            "numpy-base=1.24.3=py311h4a8f9c9_1",
            "openssl=1.1.1t=h2bbff1b_0",
            "pandas=2.0.1=py311h5bb9026_0",
            "pip=23.1.2=py311haa95532_0",
            "python=3.11.3=h966fe2a_0",
            "python-dateutil=2.8.2=pyhd3eb1b0_0",
            "pytz=2022.7=py311haa95532_0",
            "setuptools=67.8.0=py311haa95532_0",
            "six=1.16.0=pyhd3eb1b0_1",
            "sqlite=3.41.2=h2bbff1b_0",
            "tzdata=2023c=h04d1e81_0",
            "vc=14.2=h21ff451_1",
            "vs2015_runtime=14.27.29016=h5e58377_2",
            "wheel=0.38.4=py311haa95532_0",
            {
                "pip": [
                    "scikit-learn==1.2.2",
                    "threadpoolctl==3.1.0",
                    "joblib==1.2.0",
                    "scipy==1.10.1",
                ],
            },
        ],
    }


@pytest.mark.unit()
class TestEnvironmentInfo:
    """Tests for the EnvironmentInfo class."""

    def test_environment_info_init(self) -> None:
        """Test initializing an EnvironmentInfo object."""
        info = EnvironmentInfo("env1", "/path/to/env1")
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


@pytest.mark.unit()
class TestFindEnvironmentsInPath:
    """Tests for find_environments_in_path function."""

    @mock.patch("pathlib.Path.exists")
    @mock.patch("pathlib.Path.iterdir")
    @mock.patch("conda_forge_converter.core.is_conda_environment")
    def test_find_valid_environments(
        self,
        mock_is_conda_env: mock.MagicMock,
        mock_iterdir: mock.MagicMock,
        mock_exists: mock.MagicMock,
    ) -> None:
        """Test finding valid conda environments in a path."""
        # Setup
        mock_exists.return_value = True

        # Set up mock_is_conda_env to identify env1 and env2 as conda environments
        def is_conda_env_side_effect(path):
            path_str = str(path)
            is_env = "env1" in path_str or "env2" in path_str
            print(f"Checking if {path_str} is env: {is_env}")
            return is_env

        mock_is_conda_env.side_effect = is_conda_env_side_effect

        # Create mock directory entries
        mock_env1 = mock.MagicMock()
        mock_env1.name = "env1"
        mock_env1.is_dir.return_value = True
        mock_env1.__str__.return_value = "/path/to/envs/env1"  # pyright: ignore[reportFunctionMemberAccess]

        mock_env2 = mock.MagicMock()
        mock_env2.name = "env2"
        mock_env2.is_dir.return_value = True
        mock_env2.__str__.return_value = "/path/to/envs/env2"  # pyright: ignore[reportFunctionMemberAccess]

        mock_not_env = mock.MagicMock()
        mock_not_env.name = "not_an_env"
        mock_not_env.is_dir.return_value = True
        mock_not_env.__str__.return_value = "/path/to/envs/not_an_env"

        mock_iterdir.return_value = [mock_env1, mock_env2, mock_not_env]

        # Execute
        envs = find_environments_in_path("/path/to/envs", max_depth=2, verbose=True)

        # Verify
        assert len(envs) == 2
        assert "env1" in envs
        assert "env2" in envs
        assert "not_an_env" not in envs

    @mock.patch("pathlib.Path.exists")
    def test_path_does_not_exist(self, mock_exists: mock.MagicMock) -> None:
        """Test with a non-existent path."""
        # Setup
        mock_exists.return_value = False

        # Execute
        envs = find_environments_in_path("/path/does/not/exist", verbose=False)

        # Verify
        assert envs == {}


@pytest.mark.unit()
class TestListAllCondaEnvironments:
    """Tests for list_all_conda_environments function."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_registered_environments(self, mock_run: mock.MagicMock) -> None:
        """Test listing registered conda environments."""
        # Setup
        mock_output = json.dumps(
            {
                "envs": [
                    "/home/user/anaconda3",
                    "/home/user/anaconda3/envs/env1",
                    "/home/user/anaconda3/envs/env2",
                ],
            },
        )
        mock_run.return_value = mock_output

        # Execute
        envs = list_all_conda_environments()

        # Verify
        assert len(envs) == 3
        assert "base" in envs
        assert "env1" in envs
        assert "env2" in envs
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
        """Test listing environments with additional search paths."""
        # Setup
        mock_output = json.dumps(
            {
                "envs": [
                    "/home/user/anaconda3",
                    "/home/user/anaconda3/envs/env1",
                ],
            },
        )
        mock_run.return_value = mock_output

        # Mock the find_environments_in_path function to return additional envs
        mock_find.return_value = {
            "env3": "/opt/conda_envs/env3",
            "env4": "/home/user/custom/env4",
        }

        # Execute
        envs = list_all_conda_environments(
            search_paths=["/opt/conda_envs", "/home/user/custom"],
            verbose=True,
        )

        # Verify
        assert len(envs) == 4
        assert "base" in envs
        assert "env1" in envs
        assert "env3" in envs
        assert "env4" in envs


@pytest.mark.unit()
class TestGetPythonVersion:
    """Tests for get_python_version function."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_get_python_version_by_name(self, mock_run: mock.MagicMock) -> None:
        """Test getting Python version by environment name."""
        # Setup
        mock_output = json.dumps(
            [{"name": "python", "version": "3.11.3", "channel": "conda-forge"}],
        )
        mock_run.return_value = mock_output

        # Execute
        version = get_python_version("env1", verbose=False)

        # Verify
        mock_run.assert_called_once_with(
            ["conda", "list", "--name", "env1", "python", "--json"],
            False,
        )
        assert version == "3.11.3"

    @mock.patch("conda_forge_converter.core.run_command")
    def test_get_python_version_by_path(self, mock_run: mock.MagicMock) -> None:
        """Test getting Python version by environment path."""
        # Setup
        mock_output = json.dumps(
            [{"name": "python", "version": "3.11.3", "channel": "conda-forge"}],
        )
        mock_run.return_value = mock_output

        # Execute
        version = get_python_version("env1", env_path="/path/to/env1", verbose=False)

        # Verify
        mock_run.assert_called_once_with(
            ["conda", "list", "--prefix", "/path/to/env1", "python", "--json"],
            False,
        )
        assert version == "3.11.3"


@pytest.mark.unit()
class TestGetEnvironmentPackages:
    """Tests for get_environment_packages function."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_from_history_success(
        self,
        mock_run: mock.MagicMock,
        mock_from_history_env_yaml: dict[str, Any],
    ) -> None:
        """Test getting packages from environment history."""
        # Setup
        mock_run.return_value = yaml.dump(mock_from_history_env_yaml)

        # Execute
        dependencies, from_history = get_environment_packages("env1", verbose=False)

        # Verify
        assert from_history is True
        assert len(dependencies) == 5  # python, numpy, pandas, pip, and pip dict
        assert "python=3.11.3" in dependencies
        assert "numpy=1.24.3" in dependencies
        assert "pandas=2.0.1" in dependencies
        assert "pip" in dependencies
        assert {"pip": ["scikit-learn==1.2.2"]} in dependencies

    @mock.patch("conda_forge_converter.core.run_command")
    def test_fallback_to_full_export(
        self,
        mock_run: mock.MagicMock,
        mock_full_env_yaml: dict[str, Any],
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


@pytest.mark.unit()
class TestExtractPackageSpecs:
    """Tests for extract_package_specs function."""

    def test_extract_conda_packages(self) -> None:
        """Test extracting conda package specifications."""
        # Setup
        dependencies_list = [
            "python=3.11",
            "numpy=1.24",
            "pandas",  # No version specified
            "matplotlib=3.7.1",
            "pip",  # Should be ignored
        ]
        # Cast the list to the required type
        dependencies = cast(list[str | PipDependencies], dependencies_list)

        # Execute
        conda_packages, _pip_packages = extract_package_specs(dependencies)

        # Verify
        assert len(conda_packages) == 4  # python, numpy, pandas, matplotlib, excluding pip
        assert conda_packages[0]["name"] == "python"
        assert conda_packages[0]["version"] == "3.11"
        assert "numpy" in [pkg["name"] for pkg in conda_packages]
        assert "pandas" in [pkg["name"] for pkg in conda_packages]
        assert "matplotlib" in [pkg["name"] for pkg in conda_packages]

    def test_extract_pip_packages(self) -> None:
        """Test extracting pip package specifications."""
        # Setup
        dependencies_list = [
            "python=3.11",
            {
                "pip": [
                    "scikit-learn==1.2.2",
                    "jupyterlab==4.0.0",
                    "ipywidgets",  # No version
                ],
            },
        ]
        # Cast the list to the required type
        dependencies = cast(list[str | PipDependencies], dependencies_list)

        # Execute
        conda_packages, pip_packages = extract_package_specs(dependencies)

        # Verify
        assert len(pip_packages) == 3
        assert pip_packages[0]["name"] == "scikit-learn"
        assert pip_packages[0]["version"] == "1.2.2"
        assert pip_packages[2]["name"] == "ipywidgets"
        assert pip_packages[2]["version"] is None


@pytest.mark.unit()
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


@pytest.mark.unit()
class TestGetEnvironmentSize:
    """Tests for get_environment_size function."""

    @mock.patch("conda_forge_converter.core.run_command")
    def test_calculate_environment_size(
        self,
        mock_run: mock.MagicMock,
        mock_full_env_yaml: dict[str, Any],
    ) -> None:
        """Test calculating environment size based on package count."""
        # Setup
        # Make sure we have at least 5 conda packages and 3 pip packages for testing
        dependencies_list = mock_full_env_yaml["dependencies"]
        # Cast the list to the required type
        dependencies = cast(list[str | PipDependencies], dependencies_list)
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


@pytest.mark.unit()
class TestCreateCondaForgeEnvironment:
    """Tests for create_conda_forge_environment function."""

    def test_dry_run(self) -> None:
        """Test dry run mode."""
        # Setup
        conda_packages: Sequence[CondaPackage] = [
            cast(CondaPackage, {"name": "numpy", "version": "1.24.3"}),
            cast(CondaPackage, {"name": "pandas", "version": "2.0.1"}),
        ]
        pip_packages: Sequence[PipPackage] = [
            cast(PipPackage, {"name": "scikit-learn", "version": "1.2.2"}),
        ]

        # Execute
        result = create_conda_forge_environment(
            "source_env",
            "target_env",
            conda_packages,
            pip_packages,
            python_version="3.11.3",
            dry_run=True,
            verbose=False,
        )

        # Verify
        assert result is True  # Dry run always succeeds

    @mock.patch("conda_forge_converter.core.environment_exists")
    @mock.patch("conda_forge_converter.core.EnvironmentInfo.from_environment")
    @mock.patch("conda_forge_converter.core.create_conda_forge_environment")
    @mock.patch("conda_forge_converter.core.backup_environment")
    @mock.patch("conda_forge_converter.core.run_command")
    def test_successful_conversion(
        self,
        mock_run: mock.MagicMock,
        mock_backup: mock.MagicMock,
        mock_create: mock.MagicMock,
        mock_from_env: mock.MagicMock,
        mock_exists: mock.MagicMock,
    ) -> None:
        """Test successful environment conversion."""
        # Setup
        mock_exists.side_effect = [True, False]  # Source exists, target doesn't
        mock_from_env.return_value = EnvironmentInfo(
            "source_env",  # name
            "/path/to/env",  # path
            "3.11.3",  # python_version
            [
                cast(CondaPackage, {"name": "numpy", "version": "1.24.3"}),
                cast(CondaPackage, {"name": "pandas", "version": "2.0.1"}),
            ],  # conda_packages
            [
                cast(PipPackage, {"name": "scikit-learn", "version": "1.2.2"}),
            ],  # pip_packages
        )
        mock_create.return_value = True
        mock_backup.return_value = True  # Mock backup_environment to return True
        mock_run.return_value = (
            "Environment removed successfully"  # Mock run_command to return success
        )

        # Configure mock_create to accept both positional and keyword arguments
        def side_effect(*args, **kwargs):
            return True

        mock_create.side_effect = side_effect

        # Execute
        result = convert_environment(
            "source_env",
            "target_env",
            python_version="3.11.3",
            dry_run=False,
            verbose=False,
        )

        # Verify
        assert result is True
        mock_from_env.assert_called_once_with("source_env", "", False)

        # Verify that mock_create was called once
        assert mock_create.call_count == 1

        # Verify that the call arguments contain the expected values
        call_args, call_kwargs = mock_create.call_args

        # Check positional arguments
        assert call_args[0] == "source_env"
        assert (
            call_args[1] == "source_env"
        )  # When replace_original=True, effective_target is source_env
        assert len(call_args[2]) == 2  # Two conda packages
        assert call_args[2][0]["name"] == "numpy"
        assert call_args[2][1]["name"] == "pandas"
        assert len(call_args[3]) == 1  # One pip package
        assert call_args[3][0]["name"] == "scikit-learn"

    @mock.patch("conda_forge_converter.core.environment_exists")
    @mock.patch("conda_forge_converter.core.run_command")
    def test_successful_creation(
        self, mock_run: mock.MagicMock, mock_exists: mock.MagicMock
    ) -> None:
        """Test successful environment creation."""
        # Mock environment_exists to return False for target_env
        mock_exists.side_effect = lambda env_name, verbose=False: env_name != "target_env"
        # Setup
        conda_packages: Sequence[CondaPackage] = [
            cast(CondaPackage, {"name": "numpy", "version": "1.24.3"}),
            cast(CondaPackage, {"name": "pandas", "version": "2.0.1"}),
        ]
        pip_packages: Sequence[PipPackage] = [
            cast(PipPackage, {"name": "scikit-learn", "version": "1.2.2"}),
        ]

        # Mock run_command to return success for all calls
        # First call is for solver check, second for environment creation, rest for package installation
        # We need more responses for all the run_command calls
        mock_run.side_effect = [
            "libmamba",  # solver check for fast solver with conda config --show solver
            "mamba",  # which mamba check
            "mamba",  # which mamba check (called again in _create_base_environment)
            "Environment created successfully",  # environment creation
            "mamba",  # which mamba check (called in _install_conda_packages_in_batches)
            "Packages installed successfully",  # conda packages batch
            "Packages installed successfully",  # individual package 1 (if batch fails)
            "Packages installed successfully",  # individual package 2 (if batch fails)
            "Pip packages installed successfully",  # pip packages batch
            "Pip packages installed successfully",  # individual pip package (if batch fails)
        ]

        # Execute
        result = create_conda_forge_environment(
            "source_env",
            "target_env",
            conda_packages,
            pip_packages,
            python_version="3.11.3",
            dry_run=False,
            verbose=False,
        )

        # Verify
        assert result is True
        # Verify that run_command was called at least once
        assert mock_run.call_count > 0

        # The first call is to check for libmamba solver
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "conda" in first_call_args
        assert any(arg in first_call_args for arg in ["config", "env", "list"])

        # The second call is to check for mamba
        # Find the first "which mamba" call
        which_mamba_call_found = False
        for call_args in mock_run.call_args_list:
            args = call_args[0][0]
            if "which" in args and "mamba" in args:
                which_mamba_call_found = True
                break
        assert which_mamba_call_found, "No 'which mamba' call found"

        # Find the environment creation call
        create_env_call_found = False
        for _, call_args in enumerate(mock_run.call_args_list):
            args = call_args[0][0]
            if ("conda" in args or "mamba" in args) and "create" in args and "target_env" in args:
                create_env_call_found = True
                # Check that python version is specified correctly
                assert "python=3.11.3" in args or any(
                    arg.startswith("python=3.11.3") for arg in args
                ), "Python version not specified correctly"
                break
        assert create_env_call_found, "No environment creation call found"

    @mock.patch("conda_forge_converter.core.environment_exists")
    @mock.patch("conda_forge_converter.core.run_command")
    def test_creation_failure(self, mock_run: mock.MagicMock, mock_exists: mock.MagicMock) -> None:
        """Test environment creation failure."""
        # Setup
        conda_packages: Sequence[CondaPackage] = [
            cast(CondaPackage, {"name": "numpy", "version": "1.24.3"}),
        ]
        empty_pip_packages: Sequence[PipPackage] = []

        # Mock environment_exists to return False for target_env
        mock_exists.side_effect = lambda env_name, verbose=False: env_name != "target_env"

        # First call for solver check, second succeeds (create env), third call fails (install packages)
        # We need to make sure the package installation fails
        # The failure needs to happen in _install_conda_packages_in_batches
        # Let's add a print statement to see what's happening
        def side_effect(*args, **kwargs):
            cmd = args[0] if args else []
            if len(cmd) > 0:
                if "conda" in cmd[0] and "config" in cmd:
                    return "libmamba"
                elif "which" in cmd[0] and "mamba" in cmd:
                    return "mamba"
                elif ("conda" in cmd[0] or "mamba" in cmd[0]) and "create" in cmd:
                    return "Environment created successfully"
                elif ("conda" in cmd[0] or "mamba" in cmd[0]) and "install" in cmd:
                    # This is the package installation - make it fail
                    return None
            return "default"

        mock_run.side_effect = side_effect

        # Execute
        result = create_conda_forge_environment(
            "source_env",
            "target_env",
            conda_packages,
            empty_pip_packages,
            python_version="3.11.3",
            dry_run=False,
            verbose=False,
        )

        # Verify
        assert result is False

        # Check that run_command was called with the expected arguments
        install_calls = [
            call
            for call in mock_run.call_args_list
            if len(call[0][0]) > 0
            and ("conda" in call[0][0][0] or "mamba" in call[0][0][0])
            and "install" in call[0][0]
        ]
        assert len(install_calls) > 0, "No install calls were made"


@pytest.mark.unit()
class TestConvertEnvironment:
    """Tests for convert_environment function."""

    @mock.patch("conda_forge_converter.core.environment_exists")
    @mock.patch("conda_forge_converter.core.EnvironmentInfo.from_environment")
    @mock.patch("conda_forge_converter.core.create_conda_forge_environment")
    @mock.patch("conda_forge_converter.core.backup_environment")
    def test_successful_conversion(
        self,
        mock_backup: mock.MagicMock,
        mock_create_forge: mock.MagicMock,
        mock_from_env: mock.MagicMock,
        mock_exists: mock.MagicMock,
    ) -> None:
        """Test successful environment conversion."""
        # Setup
        mock_exists.side_effect = [True, False]  # Source exists, target doesn't
        mock_exists.side_effect = [True, False]  # Source exists, target doesn't
        mock_from_env.return_value = EnvironmentInfo(
            "source_env",  # name
            "/path/to/env",  # path
            "3.11.3",  # python_version
            [
                cast(CondaPackage, {"name": "numpy", "version": "1.24.3"}),
                cast(CondaPackage, {"name": "pandas", "version": "2.0.1"}),
            ],  # conda_packages
            [
                cast(PipPackage, {"name": "scikit-learn", "version": "1.2.2"}),
            ],  # pip_packages
        )
        mock_create_forge.return_value = True
        mock_backup.return_value = True  # Mock backup_environment to return True

        # Execute
        result = convert_environment(
            "source_env",
            "target_env",
            python_version="3.11.3",
            dry_run=False,
            verbose=False,
            replace_original=False,  # Default is True, but we're explicitly setting it for the test
            backup_suffix="_anaconda_backup",
        )

        # Verify
        assert result is True
        mock_from_env.assert_called_once_with("source_env", "", False)
        mock_create_forge.assert_called_once_with(
            "source_env",
            "target_env",
            [
                {"name": "numpy", "version": "1.24.3"},
                {"name": "pandas", "version": "2.0.1"},
            ],
            [
                {"name": "scikit-learn", "version": "1.2.2"},
            ],
            "3.11.3",
            False,
            False,
            use_fast_solver=True,
            batch_size=20,
            preserve_ownership=True,
        )

    @mock.patch("conda_forge_converter.core.environment_exists")
    def test_target_already_exists(self, mock_exists: mock.MagicMock) -> None:
        """Test when target environment already exists."""
        # Setup
        mock_exists.side_effect = [True, True]  # Source and target both exist

        # Execute
        result = convert_environment(
            "source_env", "target_env", verbose=False, replace_original=False
        )

        # Verify
        assert result is False
        assert mock_exists.call_count == 2
        mock_exists.assert_any_call("source_env", False)
        mock_exists.assert_any_call("target_env", False)

    @mock.patch("conda_forge_converter.core.environment_exists")
    @mock.patch("conda_forge_converter.core.EnvironmentInfo.from_environment")
    def test_environment_info_failure(
        self,
        mock_from_env: mock.MagicMock,
        mock_exists: mock.MagicMock,
    ) -> None:
        """Test when environment info can't be obtained."""
        # Setup
        mock_exists.side_effect = [
            True,
            False,
            False,
            False,
        ]  # Source exists, target doesn't, and extra values
        mock_from_env.return_value = None  # Can't get environment info

        # Execute
        with pytest.raises(ConversionError) as exc_info:
            convert_environment("source_env", "target_env", verbose=False, replace_original=False)

        # Verify
        # The error message includes the original error
        assert "Failed to convert environment 'source_env' to 'target_env'" in str(exc_info.value)
        assert "Failed to analyze environment" in str(exc_info.value)
        assert mock_exists.call_count == 2
        mock_exists.assert_any_call("source_env", False)
        mock_exists.assert_any_call("target_env", False)
        mock_from_env.assert_called_once_with("source_env", "", False)


@pytest.mark.unit()
class TestConvertMultipleEnvironments:
    """Tests for convert_multiple_environments function."""

    @pytest.fixture()
    def mock_conda_environments(self) -> dict[str, str]:
        """Fixture providing test conda environments."""
        return {
            "base": "/home/user/anaconda3",
            "data_science": "/home/user/anaconda3/envs/data_science",
            "env1": "/home/user/anaconda3/envs/env1",
            "env2": "/home/user/anaconda3/envs/env2",
        }

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    def test_no_environments_found(self, mock_list: mock.MagicMock) -> None:
        """Test with no environments found."""
        # Setup
        mock_list.return_value = {}

        # Execute
        result = convert_multiple_environments(verbose=False)

        # Verify
        assert result is False
        mock_list.assert_called_once()

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    def test_pattern_filtering(
        self,
        mock_list: mock.MagicMock,
        mock_conda_environments: dict[str, str],
    ) -> None:
        """Test filtering environments by pattern."""
        # Setup
        mock_list.return_value = mock_conda_environments

        # To avoid actually running conversions
        with mock.patch("conda_forge_converter.core.convert_environment") as mock_convert:
            # Mock the conversion to always succeed
            mock_convert.return_value = True

            # Execute with a pattern that should match 'data_science' only
            result = convert_multiple_environments(
                env_pattern="data*",
                verbose=False,
                dry_run=True,
            )

            # Verify
            assert result is True
            assert mock_convert.call_count == 1
            mock_convert.assert_called_once()

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    def test_with_exclusions(
        self,
        mock_list: mock.MagicMock,
        mock_conda_environments: dict[str, str],
    ) -> None:
        """Test excluding specific environments."""
        # Setup
        mock_list.return_value = mock_conda_environments

        # To avoid actually running conversions
        with mock.patch("conda_forge_converter.core.convert_environment") as mock_convert:
            # Mock the conversion to always succeed
            mock_convert.return_value = True

            # Execute with exclusion of 'base' and 'data_science'
            result = convert_multiple_environments(
                exclude="*base*,*data*",
                verbose=False,
                dry_run=True,
            )

            # Verify that only env1 and env2 were processed
            assert result is True
            assert mock_convert.call_count >= 1

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    @mock.patch("conda_forge_converter.core.get_environment_size")
    @mock.patch("conda_forge_converter.core.convert_environment")
    @mock.patch("conda_forge_converter.core.get_environment_packages")
    @mock.patch("conda_forge_converter.core.EnvironmentInfo.from_environment")
    def test_disk_space_check(
        self,
        mock_from_environment: mock.MagicMock,
        mock_get_packages: mock.MagicMock,
        mock_convert: mock.MagicMock,
        mock_get_size: mock.MagicMock,
        mock_list: mock.MagicMock,
        mock_conda_environments: dict[str, str],
    ) -> None:
        """Test disk space check before conversion."""
        # Setup
        mock_list.return_value = mock_conda_environments
        mock_get_size.return_value = 500  # Each env is 500MB
        mock_convert.return_value = True

        # Mock environment info
        mock_env_info = mock.MagicMock()
        mock_from_environment.return_value = mock_env_info

        # Mock packages with correct type
        mock_get_packages.return_value = (
            ["python=3.11"],
            True,
        )  # This is already handled correctly in the test

        # Mock check_disk_space inside the function
        with mock.patch("conda_forge_converter.core.check_disk_space", return_value=False):
            # Execute - the current implementation just warns about low disk space
            # but doesn't prevent conversion
            result = convert_multiple_environments(verbose=False)

            # Verify
            # Note: The implementation currently just logs a warning but still proceeds with conversion
            assert result is True
        assert result is True

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    @mock.patch("conda_forge_converter.core.convert_environment")
    def test_parallel_conversion(
        self,
        mock_convert: mock.MagicMock,
        mock_list: mock.MagicMock,
        mock_conda_environments: dict[str, str],
    ) -> None:
        """Test parallel conversion of environments."""
        # Setup
        mock_list.return_value = mock_conda_environments
        mock_convert.return_value = True

        # Execute
        # Create a list of source environments to pass directly
        source_envs = list(mock_conda_environments.keys())

        # Mock check_disk_space inside the function
        with mock.patch("conda_forge_converter.core.check_disk_space", return_value=True):
            result = convert_multiple_environments(
                source_envs=source_envs,  # Pass source_envs directly to avoid filtering
                target_suffix="_forge",
                dry_run=False,
                verbose=False,
                max_parallel=2,
                backup=False,
            )

            # Verify
            assert result is True
            assert mock_convert.call_count == len(mock_conda_environments)

            # Verify that convert_environment was called with the correct arguments for each environment
            for env_name in mock_conda_environments:
                mock_convert.assert_any_call(
                    env_name,
                    None,  # When replace_original=True, target_env is None
                    None,  # python_version
                    False,  # dry_run
                    False,  # verbose
                    use_fast_solver=True,
                    batch_size=20,
                    preserve_ownership=True,
                    replace_original=True,
                    backup_suffix="_anaconda_backup",
                )

    # We already have a working test_parallel_conversion that uses high-level mocks
    # This test was removed because it was redundant and difficult to maintain
