"""Core functionality for the conda-forge-converter package."""

import datetime
import fnmatch
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Annotated,
    Self,
    TypeAlias,
    TypedDict,
    cast,
)

# Import yaml with proper error handling
try:
    import yaml
    from yaml import YAMLError
except ImportError:
    raise ImportError(
        "PyYAML is required for this application. Please install it with: pip install pyyaml"
    )

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


# YAML environment structure types
class PipDependencies(TypedDict):
    """Represents pip dependencies section in environment.yml."""

    pip: list[str]


class EnvironmentYaml(TypedDict):
    """Represents the structure of environment.yml files."""

    name: str
    channels: list[str]
    dependencies: list[str | PipDependencies]


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
) -> tuple[list[str | PipDependencies], bool]:
    """Get a list of packages in a conda environment.

    Args:
    ----
        env_name: Name of the environment
        env_path: Path to the environment, if not using a named environment
        verbose: Whether to log detailed information

    Returns:
    -------
        Tuple of (list of dependencies, from_history flag)
        The from_history flag indicates if we got the environment from history

    Raises:
    ------
        RuntimeError: If unable to export environment data using conda commands

    """
    # Prepare base command based on whether we have a path or just a name
    if env_path:
        base_cmd = ["conda", "env", "export", "--prefix", str(env_path)]
        env_identifier = f"at path {env_path}"
    else:
        base_cmd = ["conda", "env", "export", "--name", env_name]
        env_identifier = f"named '{env_name}'"

    # Try with --from-history first
    output = run_command(base_cmd + ["--from-history"], verbose)

    if is_command_output_str(output):
        try:
            env_yaml: EnvironmentYaml = yaml.safe_load(output)
            dependencies = env_yaml.get("dependencies", [])
            if dependencies:
                logger.debug(f"Successfully exported environment {env_identifier} with history")
                return dependencies, True
            logger.warning(f"Environment {env_identifier} has no dependencies in history")
        except YAMLError as e:
            logger.error(f"Error parsing YAML output from conda env export: {str(e)}")

    # If --from-history fails, try regular export
    logger.warning("Could not get environment history.")
    logger.warning("Attempting to use regular environment export instead.")
    logger.warning("Note: This may include dependencies that were not directly installed.")

    output = run_command(base_cmd, verbose)

    if is_command_output_str(output):
        try:
            env_yaml: EnvironmentYaml = yaml.safe_load(output)
            dependencies = env_yaml.get("dependencies", [])
            if dependencies:
                logger.debug(f"Successfully exported environment {env_identifier}")
                return dependencies, False
            logger.warning(f"Environment {env_identifier} has no dependencies")
        except YAMLError as e:
            logger.error(f"Error parsing YAML output from conda env export: {str(e)}")
            raise RuntimeError(f"Failed to parse conda environment {env_identifier}: {str(e)}")

    error_msg = (
        f"Failed to export environment {env_identifier}. Make sure it exists and is accessible."
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def extract_package_specs(
    dependencies: list[str | PipDependencies],
) -> tuple[CondaPackages, PipPackages]:
    """Extract package specifications from conda environment export data.

    Parses the raw environment data to extract conda and pip package specs.

    Args:
    ----
        dependencies: List of dependencies from environment.yml or conda env export

    Returns:
    -------
        Tuple containing (conda_packages, pip_packages) where each is a list of
        dicts with 'name' and 'version' keys

    """
    conda_packages: CondaPackages = []
    pip_packages: PipPackages = []

    if not dependencies:
        logger.warning("No dependencies provided to extract package specifications")
        return conda_packages, pip_packages

    # Process main conda packages
    for dep in dependencies:
        if isinstance(dep, str):
            # Simple string dependency like "numpy=1.19.2" or just "numpy"
            parts = dep.split("=", 1)
            pkg_name = parts[0].strip()
            pkg_version = parts[1].strip() if len(parts) > 1 else None

            # Skip conda channels and metapackages
            if pkg_name not in [
                "conda-forge",
                "defaults",
                "pip",
                "conda",
            ] and not pkg_name.startswith("_"):
                conda_packages.append({"name": pkg_name, "version": pkg_version})
        elif isinstance(dep, dict) and "pip" in dep:
            # Process pip packages section
            pip_deps = cast(PipDependencies, dep)
            for pip_dep in pip_deps["pip"]:
                if isinstance(pip_dep, str):
                    # Handle pip packages with format "package==version" or just "package"
                    parts = pip_dep.split("==", 1)
                    pip_name = parts[0].strip()
                    pip_version = parts[1].strip() if len(parts) > 1 else None

                    pip_packages.append({"name": pip_name, "version": pip_version})

    if not conda_packages and not pip_packages:
        logger.warning("No valid packages found in dependencies")

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
        logger.warning(f"Failed to get environment information for '{env_name}'")
        return 0

    # Crude estimation based on the number of packages
    try:
        env_yaml: EnvironmentYaml = yaml.safe_load(output)
        dependencies = env_yaml.get("dependencies", [])

        # Count pip packages
        pip_count = 0
        for dep in dependencies:
            if isinstance(dep, dict) and "pip" in dep:
                pip_deps = cast(PipDependencies, dep)
                pip_count += len(pip_deps["pip"])

        # Count conda packages
        conda_count = sum(1 for dep in dependencies if isinstance(dep, str))

        total_packages = conda_count + pip_count
        if verbose:
            logger.debug(
                f"Environment '{env_name}' has {conda_count} conda packages and {pip_count} pip packages"
            )

        # Rough estimate: 50MB per package on average
        return total_packages * 50
    except Exception as e:
        logger.error(f"Error estimating environment size: {str(e)}")
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

    Steps:
    1. Create a new environment with Python
    2. Install conda packages from conda-forge
    3. Install pip packages

    Args:
        source_env: Name of the source environment
        target_env: Name of the target environment
        conda_packages: List of conda packages to install
        pip_packages: List of pip packages to install
        python_version: Python version to use (defaults to source env's version)
        dry_run: If True, only simulate the operation
        verbose: Whether to log detailed information

    Returns:
        True if the operation succeeded, False otherwise

    """
    if dry_run:
        # Log what would be created
        logger.info(f"Would create conda-forge environment: {target_env}")
        logger.info(f"Based on: {source_env}")

        if python_version:
            logger.info(f"Python version: {python_version}")

        if conda_packages:
            logger.info(f"Conda packages to install ({len(conda_packages)}):")
            for pkg in conda_packages[:10]:  # Show first 10 only
                version_str = f"={pkg['version']}" if pkg["version"] else ""
                logger.info(f"  {pkg['name']}{version_str}")
            if len(conda_packages) > 10:
                logger.info(f"  ... and {len(conda_packages) - 10} more")

        if pip_packages:
            logger.info(f"Pip packages to install ({len(pip_packages)}):")
            for pkg in pip_packages[:10]:  # Show first 10 only
                version_str = f"=={pkg['version']}" if pkg["version"] else ""
                logger.info(f"  {pkg['name']}{version_str}")
            if len(pip_packages) > 10:
                logger.info(f"  ... and {len(pip_packages) - 10} more")

        return True

    # Check if environment already exists
    if environment_exists(target_env, verbose):
        logger.error(f"Environment '{target_env}' already exists")
        return False

    # 1. Create base environment with Python
    if _create_base_environment(target_env, python_version, verbose) is False:
        return False

    # 2. Install conda packages
    if conda_packages and not _install_conda_packages(target_env, conda_packages, verbose):
        return False

    # 3. Install pip packages
    if pip_packages and not _install_pip_packages(target_env, pip_packages, verbose):
        return False

    logger.info(f"Successfully created conda-forge environment '{target_env}'")
    return True


def _create_base_environment(target_env: str, python_version: str | None, verbose: bool) -> bool:
    """Create the base environment with Python."""
    create_cmd = ["conda", "create", "--name", target_env, "--channel", "conda-forge", "--yes"]

    # Add Python version if specified
    if python_version:
        create_cmd.append(f"python={python_version}")
    else:
        create_cmd.append("python")

    result = run_command(create_cmd, verbose)
    if not result:
        logger.error(f"Failed to create environment '{target_env}'")
        return False
    return True


def _install_conda_packages(target_env: str, conda_packages: CondaPackages, verbose: bool) -> bool:
    """Install conda packages into the target environment."""
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
            "--yes",
        ]
        install_cmd.extend(conda_pkg_specs)
        result = run_command(install_cmd, verbose)
        if not result:
            logger.error(f"Failed to install conda packages in '{target_env}'")
            return False
    return True


def _install_pip_packages(target_env: str, pip_packages: PipPackages, verbose: bool) -> bool:
    """Install pip packages into the target environment."""
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

    This function performs the core conversion process from an Anaconda-based environment
    to an equivalent conda-forge environment. The process follows these steps:

    1. Validate source and target environment names
    2. Extract package specifications from the source environment
    3. Create a new environment with the same packages from conda-forge channel
    4. Install pip packages if any were present in the source environment

    The conversion prioritizes user-installed packages (via --from-history when available)
    rather than including all transitive dependencies. This results in a cleaner environment
    that more closely matches the user's intent.

    Args:
    ----
        source_env: Name of the source Anaconda environment to convert
        target_env: Name for the new conda-forge environment (defaults to source_env + "_forge")
        python_version: Specific Python version to use in the new environment. If None,
            will use the same version as the source environment.
        dry_run: If True, only shows what would be done without actually creating environments
        verbose: If True, displays detailed logging information during the conversion process
        env_path: Optional direct path to the source environment if it's not a named environment

    Returns:
    -------
        True if the conversion completed successfully, False if any errors occurred

    Raises:
    ------
        No exceptions are raised directly; errors are logged and reflected in the return value.

    Examples:
    --------
        # Basic conversion with default target name
        >>> convert_environment("data_science")
        # Would create "data_science_forge" with conda-forge packages

        # Conversion with custom target name
        >>> convert_environment("py38_env", "py38_forge")

        # Conversion with specific Python version
        >>> convert_environment("legacy_env", "modern_env", python_version="3.11")

        # Dry run to preview conversion
        >>> convert_environment("my_env", dry_run=True, verbose=True)

        # Convert environment located at a specific path
        >>> convert_environment("custom_env", env_path="/path/to/env")

    Notes:
    -----
        - If the target environment already exists, the conversion will be skipped.
        - Non-conda packages (installed via pip) will be carried over to the new environment.
        - The function attempts to use --from-history to only convert directly installed
          packages, falling back to the full dependency list if history is not available.

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
    # Get and filter environments
    env_dict, envs_to_convert = _get_and_filter_environments(
        env_pattern, exclude, search_paths, verbose
    )
    if not envs_to_convert:
        return False

    # Create backup directory if needed
    backup_dir = _create_backup_directory(backup, dry_run)

    # Check disk space
    _check_disk_space()

    # Process environments and collect results
    results = _process_environments(
        env_dict, envs_to_convert, target_suffix, dry_run, verbose, max_parallel, backup_dir
    )

    # Log results summary
    _log_results_summary(results, verbose)

    # Return True if all attempted conversions were successful (ignoring skipped)
    success_count = len(results["success"])
    failed_count = len(results["failed"])
    return failed_count == 0 and success_count > 0


def _get_and_filter_environments(
    env_pattern: str | None, exclude: str | None, search_paths: list[PathLike] | None, verbose: bool
) -> tuple[EnvMapping, list[str]]:
    """Get all environments and filter them based on patterns.

    Args:
        env_pattern: Pattern to match environment names
        exclude: Pattern to exclude environment names
        search_paths: Additional paths to search
        verbose: Whether to log detailed information

    Returns:
        Tuple of (env_dict, envs_to_convert)

    """
    # Get all available environments
    env_dict = list_all_conda_environments(search_paths, verbose)
    if not env_dict:
        logger.error("No conda environments found")
        return {}, []

    # Filter environments by pattern
    if env_pattern:
        envs_to_convert = [name for name in env_dict if fnmatch.fnmatch(name, env_pattern)]
    else:
        envs_to_convert = list(env_dict.keys())

    # Exclude environments by pattern
    if exclude:
        # Handle comma-separated exclude patterns
        exclude_patterns = [p.strip() for p in exclude.split(",")]
        for pattern in exclude_patterns:
            envs_to_convert = [
                name for name in envs_to_convert if not fnmatch.fnmatch(name, pattern)
            ]

    # Check if we have any environments to convert
    if not envs_to_convert:
        logger.error("No environments match the specified criteria")
        return env_dict, []

    logger.info(f"Found {len(envs_to_convert)} environments to convert")
    return env_dict, envs_to_convert


def _create_backup_directory(backup: bool, dry_run: bool) -> str | None:
    """Create a backup directory for environment specifications.

    Args:
        backup: Whether to backup environment specs
        dry_run: Whether this is a dry run

    Returns:
        Path to backup directory or None if backup not needed

    """
    if not backup or dry_run:
        return None

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"conda_env_backups_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    logger.info(f"Backing up environment specifications to {backup_dir}")
    return backup_dir


def _check_disk_space() -> None:
    """Check if there's enough disk space available."""
    if not check_disk_space(needed_gb=5):
        logger.warning(
            "Not enough disk space available. Required: 5 GB minimum. "
            "You might run out of space during the conversion."
        )


def _backup_environment(env_name: str, backup_dir: str | None, verbose: bool) -> None:
    """Backup environment specification to a file.

    Args:
        env_name: Name of environment to backup
        backup_dir: Directory to store backup
        verbose: Whether to log detailed information

    """
    if not backup_dir:
        return

    output = run_command(["conda", "env", "export", "--name", env_name, "--no-builds"], verbose)

    if not is_command_output_str(output):
        logger.warning(f"Failed to export environment '{env_name}'")
        return

    backup_file = os.path.join(backup_dir, f"{env_name}.yml")
    try:
        with open(backup_file, "w") as f:
            f.write(output)
        if verbose:
            logger.debug(f"Backed up environment '{env_name}' to {backup_file}")
    except Exception as e:
        logger.warning(f"Failed to write backup for '{env_name}': {e}")


def _process_environments(
    env_dict: EnvMapping,
    envs_to_convert: list[str],
    target_suffix: str,
    dry_run: bool,
    verbose: bool,
    max_parallel: int,
    backup_dir: str | None,
) -> ConversionResults:
    """Process all environments for conversion.

    Args:
        env_dict: Dictionary of environment names to paths
        envs_to_convert: List of environment names to convert
        target_suffix: Suffix for target environment names
        dry_run: Whether this is a dry run
        verbose: Whether to log detailed information
        max_parallel: Maximum number of parallel conversions
        backup_dir: Directory for backups or None

    Returns:
        Dictionary with conversion results

    """
    # For storing results of conversion
    results: ConversionResults = {
        "success": [],
        "failed": [],
        "skipped": [],
    }

    # Keep track of processed environments
    processed_envs: set[str] = set()
    total_count = len(envs_to_convert)

    def process_environment(source_env: str) -> None:
        """Process a single environment for conversion."""
        if source_env in processed_envs:
            return

        # Backup the environment if requested
        if backup_dir and not dry_run:
            _backup_environment(source_env, backup_dir, verbose)

        # Get the target environment name
        target_env = f"{source_env}{target_suffix}"

        # Skip if target already exists
        if environment_exists(target_env, verbose) and not dry_run:
            results["skipped"].append((source_env, f"Target '{target_env}' already exists"))
            logger.info(f"Skipping '{source_env}': Target '{target_env}' already exists")
            processed_envs.add(source_env)
            return

        # Get environment size for logging
        if not dry_run and verbose:
            size_mb = get_environment_size(source_env, False) / (1024 * 1024)
            logger.info(f"Converting '{source_env}' (estimated size: {size_mb:.1f} MB)")

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

        # Log progress
        completed = len(processed_envs)
        logger.info(f"Progress: {completed}/{total_count} environments processed")

    # Process environments (in parallel if requested)
    if max_parallel > 1 and not dry_run:
        logger.info(f"Converting environments using {max_parallel} parallel processes")
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            list(executor.map(process_environment, envs_to_convert))
    else:
        for env in envs_to_convert:
            process_environment(env)

    return results


def _log_results_summary(results: ConversionResults, verbose: bool) -> None:
    """Log summary of conversion results.

    Args:
        results: Dictionary with conversion results
        verbose: Whether to log detailed information

    """
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
