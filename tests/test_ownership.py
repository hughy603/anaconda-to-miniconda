"""Tests for the ownership preservation functionality."""

from unittest import mock

from conda_forge_converter.core import (
    create_conda_forge_environment,
)
from conda_forge_converter.utils import (
    change_path_owner,
    get_owner_names,
    get_path_owner,
    is_root,
)


class TestOwnershipUtils:
    """Tests for ownership utility functions."""

    def test_is_root(self):
        """Test the is_root function."""
        # Skip test on Windows
        import sys

        if sys.platform.startswith("win"):
            return

        with mock.patch("os.geteuid") as mock_geteuid:
            # Test when running as root
            mock_geteuid.return_value = 0
            assert is_root() is True

            # Test when not running as root
            mock_geteuid.return_value = 1000
            assert is_root() is False

    def test_get_path_owner(self):
        """Test the get_path_owner function."""
        with mock.patch("pathlib.Path.stat") as mock_stat:
            # Setup mock stat result
            mock_stat_result = mock.MagicMock()
            mock_stat_result.st_uid = 1000
            mock_stat_result.st_gid = 1000
            mock_stat.return_value = mock_stat_result

            # Test function
            uid, gid = get_path_owner("/path/to/env")
            assert uid == 1000
            assert gid == 1000

    def test_get_owner_names(self):
        """Test the get_owner_names function."""
        # Skip test on Windows
        import sys

        if sys.platform.startswith("win"):
            # On Windows, get_owner_names should always return ("unknown", "unknown")
            username, groupname = get_owner_names(1000, 1000)
            assert username == "unknown"
            assert groupname == "unknown"
            return

        # On Unix-like systems, test the actual functionality
        with (
            mock.patch("pwd.getpwuid") as mock_getpwuid,
            mock.patch("grp.getgrgid") as mock_getgrgid,
        ):
            # Setup mocks
            mock_pwd = mock.MagicMock()
            mock_pwd.pw_name = "testuser"
            mock_getpwuid.return_value = mock_pwd

            mock_grp = mock.MagicMock()
            mock_grp.gr_name = "testgroup"
            mock_getgrgid.return_value = mock_grp

            # Test function
            username, groupname = get_owner_names(1000, 1000)
            assert username == "testuser"
            assert groupname == "testgroup"

            # Test with KeyError
            mock_getpwuid.side_effect = KeyError("No such user")
            username, groupname = get_owner_names(9999, 9999)
            assert username == "unknown"
            assert groupname == "unknown"

    def test_change_path_owner(self):
        """Test the change_path_owner function."""
        # Skip test on Windows
        import sys

        if sys.platform.startswith("win"):
            # On Windows, change_path_owner should always return True
            result = change_path_owner("/path/to/env", 1000, 1000)
            assert result is True
            return

        # On Unix-like systems, test the actual functionality
        with mock.patch("os.chown") as mock_chown, mock.patch("os.walk") as mock_walk:
            # Setup mock for os.walk
            mock_walk.return_value = [
                ("/path/to/env", ["bin", "lib"], ["file1.txt", "file2.txt"]),
                ("/path/to/env/bin", [], ["python"]),
                ("/path/to/env/lib", [], ["lib1.so", "lib2.so"]),
            ]

            # Test recursive change
            result = change_path_owner("/path/to/env", 1000, 1000)
            assert result is True
            assert mock_chown.call_count > 1  # Should be called multiple times

            # Test non-recursive change
            mock_chown.reset_mock()
            result = change_path_owner("/path/to/env/file.txt", 1000, 1000, recursive=False)
            assert result is True
            assert mock_chown.call_count == 1  # Should be called once

            # Test error handling
            mock_chown.side_effect = PermissionError("Permission denied")
            result = change_path_owner("/path/to/env", 1000, 1000)
            assert result is False


class TestOwnershipPreservation:
    """Tests for ownership preservation in environment conversion."""

    @mock.patch("conda_forge_converter.core.environment_exists")
    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    @mock.patch("conda_forge_converter.utils.get_path_owner")
    @mock.patch("conda_forge_converter.utils.get_owner_names")
    @mock.patch("conda_forge_converter.utils.change_path_owner")
    @mock.patch("conda_forge_converter.utils.is_root")
    @mock.patch("conda_forge_converter.core._create_base_environment")
    @mock.patch("conda_forge_converter.core._install_conda_packages_in_batches")
    @mock.patch("conda_forge_converter.core._install_pip_packages_in_batches")
    def test_ownership_preservation_enabled(
        self,
        mock_install_pip,
        mock_install_conda,
        mock_create_base,
        mock_is_root,
        mock_change_owner,
        mock_get_names,
        mock_get_owner,
        mock_list_envs,
        mock_exists,
    ):
        """Test that ownership is preserved when running as root with preservation enabled."""
        # Setup mocks
        mock_is_root.return_value = True
        mock_list_envs.return_value = {
            "source_env": "/path/to/source_env",
            "target_env": "/path/to/target_env",
        }
        # Mock environment_exists to return False for target_env
        mock_exists.side_effect = lambda env_name, verbose=False: env_name != "target_env"
        mock_get_owner.return_value = (1000, 1000)
        mock_get_names.return_value = ("testuser", "testgroup")
        mock_create_base.return_value = True
        mock_install_conda.return_value = True
        mock_install_pip.return_value = True
        mock_change_owner.return_value = True

        # Call function with preservation enabled
        result = create_conda_forge_environment(
            "source_env",
            "target_env",
            [],
            [],
            python_version="3.9",
            preserve_ownership=True,
        )

        # Verify
        assert result is True
        mock_change_owner.assert_called_once_with("/path/to/target_env", 1000, 1000)

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    @mock.patch("conda_forge_converter.utils.get_path_owner")
    @mock.patch("conda_forge_converter.utils.get_owner_names")
    @mock.patch("conda_forge_converter.utils.change_path_owner")
    @mock.patch("conda_forge_converter.utils.is_root")
    @mock.patch("conda_forge_converter.core._create_base_environment")
    @mock.patch("conda_forge_converter.core._install_conda_packages_in_batches")
    @mock.patch("conda_forge_converter.core._install_pip_packages_in_batches")
    @mock.patch("conda_forge_converter.core.environment_exists")
    def test_ownership_preservation_disabled(
        self,
        mock_exists,
        mock_install_pip,
        mock_install_conda,
        mock_create_base,
        mock_is_root,
        mock_change_owner,
        mock_get_names,
        mock_get_owner,
        mock_list_envs,
    ):
        """Test that ownership is not preserved when disabled."""
        # Setup mocks
        mock_is_root.return_value = True
        mock_list_envs.return_value = {
            "source_env": "/path/to/source_env",
            "target_env": "/path/to/target_env",
        }
        # Mock environment_exists to return False for target_env
        mock_exists.side_effect = lambda env_name, verbose=False: env_name != "target_env"
        mock_get_owner.return_value = (1000, 1000)
        mock_get_names.return_value = ("testuser", "testgroup")
        mock_create_base.return_value = True
        mock_install_conda.return_value = True
        mock_install_pip.return_value = True

        # Call function with preservation disabled
        result = create_conda_forge_environment(
            "source_env",
            "target_env",
            [],
            [],
            python_version="3.9",
            preserve_ownership=False,
        )

        # Verify
        assert result is True
        mock_change_owner.assert_not_called()

    @mock.patch("conda_forge_converter.core.list_all_conda_environments")
    @mock.patch("conda_forge_converter.utils.get_path_owner")
    @mock.patch("conda_forge_converter.utils.get_owner_names")
    @mock.patch("conda_forge_converter.utils.change_path_owner")
    @mock.patch("conda_forge_converter.utils.is_root")
    @mock.patch("conda_forge_converter.core._create_base_environment")
    @mock.patch("conda_forge_converter.core._install_conda_packages_in_batches")
    @mock.patch("conda_forge_converter.core._install_pip_packages_in_batches")
    @mock.patch("conda_forge_converter.core.environment_exists")
    def test_not_running_as_root(
        self,
        mock_exists,
        mock_install_pip,
        mock_install_conda,
        mock_create_base,
        mock_is_root,
        mock_change_owner,
        mock_get_names,
        mock_get_owner,
        mock_list_envs,
    ):
        """Test that ownership is not preserved when not running as root."""
        # Setup mocks
        mock_is_root.return_value = False
        mock_create_base.return_value = True
        mock_install_conda.return_value = True
        mock_install_pip.return_value = True
        # Mock environment_exists to return False for target_env
        mock_exists.side_effect = lambda env_name, verbose=False: env_name != "target_env"

        # Call function
        result = create_conda_forge_environment(
            "source_env",
            "target_env",
            [],
            [],
            python_version="3.9",
            preserve_ownership=True,
        )

        # Verify
        assert result is True
        mock_get_owner.assert_not_called()
        mock_change_owner.assert_not_called()
