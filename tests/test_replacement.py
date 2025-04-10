"""Tests for the environment replacement functionality."""

import unittest
from unittest.mock import patch

from conda_forge_converter.core import (
    backup_environment,
    convert_environment,
)


class TestReplacement(unittest.TestCase):
    """Test the environment replacement functionality."""

    @patch("conda_forge_converter.core.environment_exists")
    @patch("conda_forge_converter.core.run_command")
    @patch("conda_forge_converter.core.is_command_output_str")
    def test_backup_environment(self, mock_is_output_str, mock_run_command, mock_env_exists):
        """Test the backup_environment function."""
        # Setup mocks
        mock_env_exists.return_value = False
        mock_run_command.return_value = "Success"
        mock_is_output_str.return_value = True

        # Test backup creation
        result = backup_environment("myenv", "_anaconda_backup", verbose=True)
        self.assertTrue(result)
        mock_run_command.assert_called_with(
            ["conda", "create", "--name", "myenv_anaconda_backup", "--clone", "myenv", "-y"],
            True,
        )

        # Test existing backup removal
        mock_env_exists.return_value = True
        result = backup_environment("myenv", "_anaconda_backup", verbose=True)
        self.assertTrue(result)
        # First call should be to remove the existing backup
        mock_run_command.assert_any_call(
            ["conda", "env", "remove", "--name", "myenv_anaconda_backup"], True
        )
        # Second call should be to create the backup
        mock_run_command.assert_called_with(
            ["conda", "create", "--name", "myenv_anaconda_backup", "--clone", "myenv", "-y"],
            True,
        )

    @patch("conda_forge_converter.core.environment_exists")
    @patch("conda_forge_converter.core.backup_environment")
    @patch("conda_forge_converter.core.run_command")
    @patch("conda_forge_converter.core.is_command_output_str")
    @patch("conda_forge_converter.core.EnvironmentInfo.from_environment")
    @patch("conda_forge_converter.core.create_conda_forge_environment")
    def test_convert_environment_with_replacement(
        self,
        mock_create_env,
        mock_env_info,
        mock_is_output_str,
        mock_run_command,
        mock_backup,
        mock_env_exists,
    ):
        """Test the convert_environment function with replacement enabled."""
        # Setup mocks
        mock_env_exists.return_value = True
        mock_backup.return_value = True
        mock_run_command.return_value = "Success"
        mock_is_output_str.return_value = True
        mock_env_info.return_value.conda_packages = []
        mock_env_info.return_value.pip_packages = []
        mock_env_info.return_value.python_version = "3.9"
        mock_create_env.return_value = True

        # Test with replacement enabled (default)
        result = convert_environment("myenv", replace_original=True, verbose=True)
        self.assertTrue(result)

        # Verify backup was created
        mock_backup.assert_called_with("myenv", "_anaconda_backup", True)

        # Verify original environment was removed
        mock_run_command.assert_called_with(["conda", "env", "remove", "--name", "myenv"], True)

        # Verify new environment was created with original name
        mock_create_env.assert_called_with(
            "myenv",
            "myenv",
            [],
            [],
            "3.9",
            False,
            True,
            use_fast_solver=True,
            batch_size=20,
            preserve_ownership=True,
        )

    @patch("conda_forge_converter.core.environment_exists")
    @patch("conda_forge_converter.core.backup_environment")
    @patch("conda_forge_converter.core.EnvironmentInfo.from_environment")
    @patch("conda_forge_converter.core.create_conda_forge_environment")
    def test_convert_environment_without_replacement(
        self, mock_create_env, mock_env_info, mock_backup, mock_env_exists
    ):
        """Test the convert_environment function with replacement disabled."""
        # Setup mocks
        mock_env_exists.side_effect = lambda env, verbose: env == "myenv"  # Only source exists
        mock_env_info.return_value.conda_packages = []
        mock_env_info.return_value.pip_packages = []
        mock_env_info.return_value.python_version = "3.9"
        mock_create_env.return_value = True

        # Test with replacement disabled
        result = convert_environment("myenv", "myenv_forge", replace_original=False, verbose=True)
        self.assertTrue(result)

        # Verify backup was not created
        mock_backup.assert_not_called()

        # Verify new environment was created with different name
        mock_create_env.assert_called_with(
            "myenv",
            "myenv_forge",
            [],
            [],
            "3.9",
            False,
            True,
            use_fast_solver=True,
            batch_size=20,
            preserve_ownership=True,
        )


if __name__ == "__main__":
    unittest.main()
