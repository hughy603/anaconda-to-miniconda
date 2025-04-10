"""Cleanup options for original environments."""

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .utils import is_command_output_str, logger, run_command


@dataclass
class CleanupOptions:
    """Options for environment cleanup."""

    remove_original: bool = False
    backup_before_remove: bool = True
    backup_dir: str | None = None
    confirm_before_remove: bool = True
    dry_run: bool = False


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""

    env_name: str
    status: str = "pending"
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the result."""
        if not self.message:
            self.message = f"Cleanup operation for '{self.env_name}' is pending"


class EnvironmentCleanup:
    """Manage cleanup of original environments."""

    def __init__(self, options: CleanupOptions) -> None:
        """Initialize the environment cleanup manager.

        Args:
            options: Cleanup options

        """
        self.options = options

    def cleanup_environment(self, env_name: str, target_env: str | None = None) -> CleanupResult:
        """Clean up an environment.

        Args:
            env_name: Name of the environment to clean up
            target_env: Optional name of the target environment to restore to

        Returns:
            CleanupResult object containing the result of the cleanup operation

        """
        result = CleanupResult(env_name)

        try:
            # Check if environment exists
            if not self._environment_exists(env_name):
                result.status = "error"
                result.message = f"Environment '{env_name}' does not exist"
                return result

            # Create backup
            backup_result = self._create_backup(env_name)
            if not backup_result:
                result.status = "error"
                result.message = f"Failed to create backup of environment '{env_name}'"
                return result

            # Remove environment
            if not self._remove_environment(env_name):
                result.status = "error"
                result.message = f"Failed to remove environment '{env_name}'"
                return result

            # Restore to target environment if specified
            if target_env:
                restore_result = self._restore_environment(env_name, target_env)
                if not restore_result:
                    result.status = "error"
                    result.message = f"Failed to restore environment '{env_name}' to '{target_env}'"
                    return result

            result.status = "success"
            result.message = f"Successfully cleaned up environment '{env_name}'"
            if target_env:
                result.message += f" and restored to '{target_env}'"
            return result

        except Exception as e:
            result.status = "error"
            result.message = f"Error cleaning up environment '{env_name}': {e!s}"
            return result

    def cleanup_multiple_environments(
        self, env_names: list[str], target_envs: dict[str, str] | None = None
    ) -> dict[str, CleanupResult]:
        """Clean up multiple environments.

        Args:
            env_names: List of environment names to clean up
            target_envs: Dictionary mapping environment names to target environments

        Returns:
            Dictionary mapping environment names to cleanup results

        """
        results: dict[str, CleanupResult] = {}

        for env_name in env_names:
            target_env = target_envs.get(env_name) if target_envs else None
            results[env_name] = self.cleanup_environment(env_name, target_env)

        return results

    def _environment_exists(self, env_name: str) -> bool:
        """Check if an environment exists."""
        try:
            result = run_command(["conda", "env", "list", "--json"], verbose=True)
            if not isinstance(result, str):
                return False
            envs_data = json.loads(result)
            envs = envs_data.get("envs", [])
            env_paths = [Path(path).name for path in envs]
            return env_name in env_paths
        except Exception as e:
            logger.error(f"Error checking if environment exists: {e!s}")
            return False

    def _create_backup(self, env_name: str) -> bool:
        """Create a backup of an environment."""
        try:
            # Create backup directory
            backup_dir_str = str(self.options.backup_dir)
            backup_dir = Path(backup_dir_str)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Export environment
            export_path = backup_dir / f"{env_name}.yml"
            cmd = ["conda", "env", "export", "-n", env_name, "-f", str(export_path)]
            result = run_command(cmd, verbose=True)
            if not isinstance(result, str):
                return False

            # Copy environment directory
            env_path = self._get_env_path(env_name)
            if not env_path:
                logger.warning(f"Could not determine path for environment '{env_name}'")
                return False

            env_backup_dir = backup_dir / env_name
            try:
                shutil.copytree(str(env_path), str(env_backup_dir))
            except Exception as e:
                logger.error(f"Error copying environment directory: {e!s}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error creating backup: {e!s}")
            return False

    def _get_env_path(self, env_name: str) -> Path | None:
        """Get the path of an environment."""
        try:
            result = run_command(["conda", "env", "list", "--json"], verbose=True)
            if not isinstance(result, str):
                return None
            envs_data = json.loads(result)
            envs = envs_data.get("envs", [])
            for path_str in envs:
                if not isinstance(path_str, str):
                    continue
                path = Path(path_str)
                if path.name == env_name:
                    return path
            return None
        except Exception as e:
            logger.error(f"Error getting environment path: {e!s}")
            return None

    def _remove_environment(self, env_name: str) -> bool:
        """Remove an environment.

        Args:
            env_name: Name of the environment to remove

        Returns:
            True if successful, False otherwise

        """
        try:
            cmd = ["conda", "env", "remove", "-n", env_name, "-y"]
            result = run_command(cmd, verbose=True)
            return is_command_output_str(result)
        except Exception as e:
            logger.error(f"Error removing environment: {e!s}")
            return False

    def _restore_environment(self, source_env: str, target_env: str) -> bool:
        """Restore an environment from backup."""
        try:
            backup_dir_str = str(self.options.backup_dir)
            backup_dir = Path(backup_dir_str)
            backup_path = backup_dir / source_env

            if not backup_path.exists():
                logger.error(f"Backup not found for environment '{source_env}'")
                return False

            # Create new environment
            cmd = ["conda", "create", "-n", target_env, "--clone", source_env, "-y"]
            result = run_command(cmd, verbose=True)
            if not isinstance(result, str):
                return False

            return True

        except Exception as e:
            logger.error(f"Error restoring environment: {e!s}")
            return False


def create_cleanup_options(
    remove_original: bool = False,
    backup_before_remove: bool = True,
    backup_dir: str | None = None,
    confirm_before_remove: bool = True,
    dry_run: bool = False,
) -> CleanupOptions:
    """Create cleanup options.

    Args:
        remove_original: Whether to remove the original environment
        backup_before_remove: Whether to backup the environment before removal
        backup_dir: Directory to store backups
        confirm_before_remove: Whether to confirm before removal
        dry_run: Whether to perform a dry run

    Returns:
        Cleanup options

    """
    return CleanupOptions(
        remove_original=remove_original,
        backup_before_remove=backup_before_remove,
        backup_dir=backup_dir,
        confirm_before_remove=confirm_before_remove,
        dry_run=dry_run,
    )
