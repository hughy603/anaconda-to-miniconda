"""Core functionality for the conda-forge-converter package."""

import datetime
import fnmatch
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Self, TypeAlias, TypedDict, cast

import yaml  # type: ignore # noqa

from .utils import (
    PathLike,
    check_disk_space,
    is_command_output_str,
    is_conda_environment,
    logger,
    run_command,
)

# === TYPE DEFINITIONS ===


class CondaPackage(TypedDict):
    """Represents a conda package with name and optional version."""

    name: str
    version: str | None


class PipPackage(TypedDict):
    """Represents a pip package with name and optional version."""

    name: str
    version: str | None


class ConversionResults(TypedDict):
    """Results from batch environment conversion operations."""

    success: list[tuple[str, str]]  # (source_env, target_env)
    failed: list[tuple[str, str]]  # (source_env, reason)
    skipped: list[tuple[str, str]]  # (source_env, reason)


@dataclass
class EnvironmentInfo:
    """Information about a conda environment."""

    name: str
    path: str
    python_version: str | None = None
    conda_packages: list[CondaPackage] = field(default_factory=list)
    pip_packages: list[PipPackage] = field(default_factory=list)

    @classmethod
    def from_environment(cls, name: str, path: str, verbose: bool = False) -> Self | None:
        """Create an EnvironmentInfo from an existing environment.

        Args:
        ----
            name: Name of the environment
            path: Path to the environment
            verbose: Whether to log detailed information

        Returns:
        -------
            A new EnvironmentInfo object or None if the environment couldn't be analyzed

        """
        info = cls(name=name, path=path)

        # Get Python version
        info.python_version = get_python_version(name, path, verbose)

        # Get package list
        dependencies, _ = get_environment_packages(name, path, verbose)
        if not dependencies:
            return None

        # Extract package specifications
        info.conda_packages, info.pip_packages = extract_package_specs(dependencies)
        return info


# Environment mapping type
EnvMapping: TypeAlias = dict[str, str]  # name -> path

# Package specification types
PackageSpec: TypeAlias = Annotated[str, "Package specification in format name=version"]
CondaPackages: TypeAlias = list[CondaPackage]
PipPackages: TypeAlias = list[PipPackage]


# === ENVIRONMENT DISCOVERY FUNCTIONS ===


def find_environments_in_path(
    search_path: PathLike,
    max_depth: int = 3,
    verbose: bool = False,
) -> EnvMapping:
    """Find conda environments in a directory tree.

    Args:
    ----
        search_path: Root path to search for environments
        max_depth: Maximum directory depth to search
        verbose: Whether to log detailed information

    Returns:
    -------
        Dictionary mapping environment names to their paths

    """
    path_obj = Path(search_path)
    if not path_obj.exists():
        logger.warning(f"Search path does not exist: {search_path}")
        return {}

    found_envs: EnvMapping = {}

    def scan_directory(current_path: PathLike, current_depth: int) -> None:
        if current_depth > max_depth:
            return

        current_path_obj = Path(current_path)
        try:
            # Check if this path is a conda environment
            if is_conda_environment(current_path):
                env_name = current_path_obj.name
                found_envs[env_name] = str(current_path)
                if verbose:
                    logger.debug(f"Found conda environment: {env_name} at {current_path}")
                return  # Don't need to go deeper if this is an environment

            # Scan subdirectories
            for subdir in [d for d in current_path_obj.iterdir() if d.is_dir()]:
                try:
                    # Check if subdirectory is a conda environment
                    if is_conda_environment(subdir):
                        env_name = subdir.name
                        found_envs[env_name] = str(subdir)
                        if verbose:
                            logger.debug(f"Found conda environment: {env_name} at {subdir}")
                    else:
                        # Continue search in subdirectory
                        scan_directory(subdir, current_depth + 1)
                except (PermissionError, OSError):
                    if verbose:
                        logger.debug(f"Skipping directory due to permission error: {subdir}")
        except (PermissionError, OSError):
            if verbose:
                logger.debug(f"Skipping directory due to permission error: {current_path}")

    # Start scanning
    scan_directory(search_path, 0)

    if verbose and found_envs:
        logger.info(f"Found {len(found_envs)} conda environments in {search_path}")

    return found_envs


def list_all_conda_environments(
    search_paths: list[PathLike] | None = None,
    verbose: bool = False,
) -> EnvMapping:
    """List all conda environments on the system and in specified search paths.

    Args:
    ----
        search_paths: Additional paths to search for environments
        verbose: Whether to log detailed information

    Returns:
    -------
        Dictionary mapping environment names to their paths

    """
    env_dict: EnvMapping = {}

    # Get registered environments through conda command
    output = run_command(["conda", "env", "list", "--json"], verbose)
    if is_command_output_str(output):
        try:
            env_data = json.loads(output)
            for env_path in env_data.get("envs", []):
                env_path_obj = Path(env_path)

                # Special case for the base environment (main Anaconda/Miniconda installation)
                # Parse based on path structure
                if env_path_obj.name in ["anaconda3", "miniconda3"]:
                    env_name = "base"
                # Handle paths inside the envs directory of base installation
                elif env_path_obj.parent.name == "envs":
                    env_name = env_path_obj.name
                else:
                    env_name = env_path_obj.name

                env_dict[env_name] = env_path

            if verbose:
                logger.info(f"Found {len(env_dict)} registered conda environments")
        except json.JSONDecodeError:
            logger.error("Error parsing JSON output from conda env list")

    # Also search in additional paths if provided
    if search_paths:
        for path in search_paths:
            additional_envs = find_environments_in_path(path, verbose=verbose)
            env_dict.update(additional_envs)

    return env_dict


def environment_exists(env_name: str, verbose: bool = False) -> bool:
    """Check if a conda environment exists.

    Args:
    ----
        env_name: Name of the environment to check
        verbose: Whether to log detailed information

    Returns:
    -------
        True if the environment exists, False otherwise

    """
    env_dict = list_all_conda_environments(verbose=verbose)
    return env_name in env_dict


# === ENVIRONMENT ANALYSIS FUNCTIONS ===


def get_python_version(
    env_name: str,
    env_path: PathLike | None = None,
    verbose: bool = False,
) -> str | None:
    """Get the Python version in the specified environment.

    Args:
    ----
        env_name: Name of the environment
        env_path: Path to the environment (if known)
        verbose: Whether to log detailed information

    Returns:
    -------
        Python version string or None if it couldn't be determined

    """
    if env_path:
        # Use --prefix for custom environments
        output = run_command(
            ["conda", "list", "--prefix", str(env_path), "python", "--json"],
            verbose,
        )
    else:
        # Use --name for registered environments
        output = run_command(["conda", "list", "--name", env_name, "python", "--json"], verbose)

    if not is_command_output_str(output):
        return None

    try:
        packages = json.loads(output)
        for pkg in packages:
            if pkg["name"] == "python":
                return pkg["version"]
        return None
    except json.JSONDecodeError:
        logger.error("Error parsing JSON output from conda list")
        return None


def get_environment_packages(
    env_name: str,
    env_path: PathLike | None = None,
    verbose: bool = False,
) -> tuple[list[Any], bool]:
    """Get packages that were explicitly installed by the user.

    Args:
    ----
        env_name: Name of the environment
        env_path: Path to the environment (if known)
        verbose: Whether to log detailed information

    Returns:
    -------
        Tuple of (dependencies, from_history) where:
            - dependencies is a list of package specifications
            - from_history is True if the dependencies were from the environment history

    """
    # Prepare base command based on whether we have a path or just a name
    if env_path:
        base_cmd = ["conda", "env", "export", "--prefix", str(env_path)]
    else:
        base_cmd = ["conda", "env", "export", "--name", env_name]

    # Try with --from-history first
    output = run_command(base_cmd + ["--from-history"], verbose)

    if is_command_output_str(output):
        try:
            env_yaml = yaml.safe_load(output)
            return env_yaml.get("dependencies", []), True
        except yaml.YAMLError:
            logger.error("Error parsing YAML output from conda env export")

    # If --from-history fails, try regular export
    logger.warning("Could not get environment history.")
    logger.warning("Attempting to use regular environment export instead.")
    logger.warning("Note: This may include dependencies that were not directly installed.")

    output = run_command(base_cmd, verbose)

    if is_command_output_str(output):
        try:
            env_yaml = yaml.safe_load(output)
            return env_yaml.get("dependencies", []), False
        except yaml.YAMLError:
            logger.error("Error parsing YAML output from conda env export")

    return [], False


def extract_package_specs(dependencies: list[Any]) -> tuple[CondaPackages, PipPackages]:
    """Extract conda and pip package specifications from a dependencies list.

    Args:
    ----
        dependencies: List of package specifications (strings or dicts)

    Returns:
    -------
        Tuple of (conda_packages, pip_packages) lists

    """
    conda_packages: CondaPackages = []
    pip_packages: PipPackages = []

    # First parse the conda packages
    for dep in dependencies:
        # Handle pip sub-dependencies
        if isinstance(dep, dict) and "pip" in dep:
            for pip_spec in dep["pip"]:
                # Typically in format: package==version
                parts = pip_spec.split("==")
                name = parts[0]
                version = parts[1] if len(parts) > 1 else None
                pip_packages.append({"name": name, "version": version})
        # Regular conda dependencies
        elif isinstance(dep, str) and not dep.startswith("pip"):
            # Typically in format: package=version or package
            parts = dep.split("=", 1)  # Split on first = only
            name = parts[0]
            version = parts[1] if len(parts) > 1 else None
            conda_packages.append({"name": name, "version": version})

    # Ensure python is the first package if it exists
    python_pkg = None
    for i, pkg in enumerate(conda_packages):
        if pkg["name"] == "python":
            python_pkg = conda_packages.pop(i)
            break

    if python_pkg:
        conda_packages.insert(0, python_pkg)

    return conda_packages, pip_packages


def get_environment_size(env_name: str, verbose: bool = False) -> int:
    """Estimate the size of an environment in MB.

    Args:
    ----
        env_name: Name of the environment
        verbose: Whether to log detailed information

    Returns:
    -------
        Estimated size in megabytes

    """
    output = run_command(["conda", "env", "export", "--name", env_name], verbose)

    if not is_command_output_str(output):
        return 0

    # Crude estimation based on the number of packages
    try:
        env_yaml = yaml.safe_load(output)  # type: ignore
        env_dict = cast(dict[str, Any], env_yaml)
        dependencies = env_dict.get("dependencies", [])

        # Count pip packages
        pip_count = 0
        for dep in dependencies:
            if isinstance(dep, dict) and "pip" in dep:
                dep_dict = cast(dict[str, list[Any]], dep)
                pip_count += len(dep_dict["pip"])

        # Count conda packages
        conda_count = sum(1 for dep in dependencies if isinstance(dep, str))

        # Rough estimate: 50MB per package on average
        return (conda_count + pip_count) * 50
    except Exception:
        return 100  # Default guess if we can't parse


# === ENVIRONMENT CONVERSION FUNCTIONS ===


def create_conda_forge_environment(
    source_env: str,
    target_env: str,
    conda_packages: CondaPackages,
    pip_packages: PipPackages,
    python_version: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Create a new conda-forge environment with specified packages.

    Args:
    ----
        source_env: Source environment name (for reference)
        target_env: Target environment name
        conda_packages: List of conda packages to install
        pip_packages: List of pip packages to install
        python_version: Python version to install (if None, determined from conda_packages)
        dry_run: Whether to just log commands without executing
        verbose: Whether to log detailed information

    Returns:
    -------
        True if environment creation succeeded, False otherwise

    """
    # Log what we're doing
    logger.info(
        f"Creating conda-forge environment '{target_env}' based on '{source_env}'",
    )

    # Handle empty package lists
    if not conda_packages and not python_version:
        logger.error("No packages specified and no Python version provided")
        return False

    # Extract Python version if it wasn't explicitly provided
    if not python_version:
        for pkg in conda_packages:
            if pkg["name"] == "python" and pkg["version"] is not None:
                python_version = pkg["version"]
                break

    # Log environment creation - always do this in verbose mode
    if dry_run or verbose:
        logger.info(f"Python version: {python_version}")
        logger.info(f"Conda packages: {len(conda_packages)}")
        logger.info(f"Pip packages: {len(pip_packages)}")

    if dry_run:
        # Just log what would be done
        logger.info("Dry run - not executing commands")
        return True

    # 1. Create base environment with Python and conda-forge channels
    create_cmd = [
        "conda",
        "create",
        "--name",
        target_env,
        "--channel",
        "conda-forge",
        "--override-channels",
    ]

    # Add python if we have a version
    if python_version:
        create_cmd.extend(["python=" + python_version])

    # Only run this command if there's no existing environment
    if not environment_exists(target_env, verbose):
        result = run_command(create_cmd, verbose)
        if not result:
            logger.error(f"Failed to create environment '{target_env}'")
            return False

    # 2. Install conda packages
    if conda_packages:
        conda_pkg_specs = []
        for pkg in conda_packages:
            if pkg["name"] != "python":  # Skip python, already installed
                spec = pkg["name"]
                if pkg["version"]:
                    spec += "=" + pkg["version"]
                conda_pkg_specs.append(spec)

        if conda_pkg_specs:
            install_cmd = [
                "conda",
                "install",
                "--name",
                target_env,
                "--channel",
                "conda-forge",
                "--override-channels",
            ]
            install_cmd.extend(conda_pkg_specs)
            result = run_command(install_cmd, verbose)
            if not result:
                logger.error(f"Failed to install conda packages in '{target_env}'")
                return False

    # 3. Install pip packages
    if pip_packages:
        pip_pkg_specs = []
        for pkg in pip_packages:
            spec = pkg["name"]
            if pkg["version"]:
                spec += "==" + pkg["version"]
            pip_pkg_specs.append(spec)

        if pip_pkg_specs:
            pip_cmd = [
                "conda",
                "run",
                "--name",
                target_env,
                "pip",
                "install",
            ]
            pip_cmd.extend(pip_pkg_specs)
            result = run_command(pip_cmd, verbose)
            if not result:
                logger.error(f"Failed to install pip packages in '{target_env}'")
                return False

    logger.info(f"Successfully created conda-forge environment '{target_env}'")
    return True


def convert_environment(
    source_env: str,
    target_env: str | None = None,
    python_version: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
    env_path: PathLike | None = None,
) -> bool:
    """Convert a single environment from Anaconda to conda-forge.

    Args:
    ----
        source_env: Name of the source environment
        target_env: Name of the target environment
        python_version: Python version to use
        dry_run: Whether to simulate the operation
        verbose: Whether to log detailed information
        env_path: Path to the source environment

    Returns:
    -------
        True if the operation succeeded, False otherwise

    """
    if not target_env:
        target_env = f"{source_env}_forge"

    if environment_exists(target_env, verbose) and not dry_run:
        logger.warning(f"Target environment '{target_env}' already exists. Skipping conversion.")
        return False

    # Try to create an EnvironmentInfo
    env_info = EnvironmentInfo.from_environment(
        source_env,
        str(env_path) if env_path else source_env,
        verbose,
    )
    if not env_info:
        logger.error(f"Could not determine packages for '{source_env}'. Skipping conversion.")
        return False

    # Use provided Python version if specified, otherwise use the detected one
    if python_version:
        env_info.python_version = python_version

    if verbose:
        source_type = "top-level" if env_info.conda_packages else "all"
        logger.info(
            f"Found {len(env_info.conda_packages)} {source_type} conda packages and "
            f"{len(env_info.pip_packages)} {source_type} pip packages in '{source_env}'",
        )

    # Create new environment
    return create_conda_forge_environment(
        source_env,
        target_env,
        env_info.conda_packages,
        env_info.pip_packages,
        env_info.python_version,
        dry_run,
        verbose,
    )


def convert_multiple_environments(
    env_pattern: str | None = None,
    target_suffix: str = "_forge",
    dry_run: bool = False,
    verbose: bool = False,
    exclude: str | None = None,
    max_parallel: int = 1,
    backup: bool = True,
    search_paths: list[PathLike] | None = None,
) -> bool:
    """Convert multiple conda environments to conda-forge.

    Args:
    ----
        env_pattern: Glob pattern to match environment names
        target_suffix: Suffix to append to the target environment names
        dry_run: Whether to just log commands without executing
        verbose: Whether to log detailed information
        exclude: Glob pattern to exclude environment names
        max_parallel: Maximum number of parallel conversions to run
        backup: Whether to backup environment history files
        search_paths: Additional paths to search for environments

    Returns:
    -------
        True if all conversions succeeded, False otherwise

    """
    # Get all available environments
    env_dict = list_all_conda_environments(search_paths, verbose)
    if not env_dict:
        logger.error("No conda environments found")
        return False

    # Filter environments by pattern
    if env_pattern:
        envs_to_convert = [name for name in env_dict if fnmatch.fnmatch(name, env_pattern)]
    else:
        envs_to_convert = list(env_dict.keys())

    # Exclude environments by pattern
    if exclude:
        envs_to_convert = [name for name in envs_to_convert if not fnmatch.fnmatch(name, exclude)]

    # Check if we have any environments to convert
    if not envs_to_convert:
        logger.error("No environments match the specified criteria")
        return False

    logger.info(f"Found {len(envs_to_convert)} environments to convert")

    # Create a backup directory if needed
    backup_dir = None
    if backup and not dry_run:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"conda_env_backups_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Backing up environment specifications to {backup_dir}")

    # Check disk space
    if not check_disk_space(needed_gb=5):
        logger.warning(
            "Not enough disk space available. Required: 5 GB minimum. "
            "You might run out of space during the conversion.",
        )

    # For storing results of conversion
    results: ConversionResults = {
        "success": [],
        "failed": [],
        "skipped": [],
    }

    # Keep track of processed environments
    processed_envs: set[str] = set()

    def process_environment(source_env: str) -> None:
        """Process a single environment for conversion.

        Args:
        ----
            source_env: Name of the source environment to process

        """
        if source_env in processed_envs:
            return

        # Get the target environment name
        target_env = f"{source_env}{target_suffix}"

        # Check if target already exists
        if environment_exists(target_env, verbose):
            results["skipped"].append((source_env, f"Target '{target_env}' already exists"))
            logger.info(f"Skipping '{source_env}': Target '{target_env}' already exists")
            return

        # Run the conversion
        success = convert_environment(
            source_env,
            target_env,
            dry_run=dry_run,
            verbose=verbose,
            env_path=env_dict.get(source_env),
        )

        # Track results
        if success:
            results["success"].append((source_env, target_env))
            logger.info(f"Successfully converted '{source_env}' to '{target_env}'")
        else:
            results["failed"].append((source_env, "Conversion failed"))
            logger.error(f"Failed to convert '{source_env}' to '{target_env}'")

        # Mark as processed
        processed_envs.add(source_env)

    # Process environments (in parallel if requested)
    if max_parallel > 1 and not dry_run:
        logger.info(f"Converting environments using {max_parallel} parallel processes")
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            list(executor.map(process_environment, envs_to_convert))
    else:
        for env in envs_to_convert:
            process_environment(env)

    # Log summary
    success_count = len(results["success"])
    failed_count = len(results["failed"])
    skipped_count = len(results["skipped"])

    logger.info("=" * 40)
    logger.info("Conversion Summary:")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  Skipped: {skipped_count}")
    logger.info("=" * 40)

    if verbose and results["success"]:
        logger.info("Successful conversions:")
        for src, tgt in results["success"]:
            logger.info(f"  {src} -> {tgt}")

    if results["failed"]:
        logger.warning("Failed conversions:")
        for src, reason in results["failed"]:
            logger.warning(f"  {src}: {reason}")

    if results["skipped"] and verbose:
        logger.info("Skipped conversions:")
        for src, reason in results["skipped"]:
            logger.info(f"  {src}: {reason}")

    # Return True if all attempted conversions were successful (ignoring skipped)
    return failed_count == 0 and success_count > 0


def is_conda_environment(path: PathLike) -> bool:
    """Check if a directory is a conda environment.

    Args:
    ----
        path: Path to the directory to check.

    Returns:
    -------
        True if the directory appears to be a conda environment.

    """
    path_obj = Path(path)

    # A conda environment typically has these subdirectories
    conda_meta = path_obj / "conda-meta"

    # Different paths based on OS
    is_windows = sys.platform.startswith("win")
    if is_windows:
        bin_dir = path_obj / "Scripts"
        python_exec = path_obj / "python.exe"
    else:
        bin_dir = path_obj / "bin"
        python_exec = bin_dir / "python"

    # If conda-meta exists and either python or bin/Scripts exists, it's likely a conda env
    return conda_meta.exists() and (python_exec.exists() or bin_dir.exists())
