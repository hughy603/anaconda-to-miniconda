"""Core functionality for the conda-forge-converter package.

This module contains the main functionality for converting Anaconda environments
to conda-forge environments. It provides classes and functions for environment
discovery, package analysis, and environment creation.

The module is organized into the following functional areas:

Type Definitions:
  - CondaPackage: Represents a conda package with name and optional version
  - PipPackage: Represents a pip package with name and optional version
  - ConversionResults: Results from batch environment conversion operations
  - PipDependencies: Represents pip dependencies section in environment.yml
  - EnvironmentYaml: Represents the structure of environment.yml files
  - EnvironmentInfo: Information about a conda environment

Environment Discovery:
  - discover_environments: Find conda environments on the system
  - list_all_conda_environments: List all conda environments
  - is_conda_environment: Check if a directory is a conda environment

Package Analysis:
  - extract_packages: Extract package information from environment data
  - separate_conda_pip_packages: Separate conda and pip packages
  - analyze_environment: Analyze an environment and extract package information

Environment Creation:
  - create_environment: Create a new conda environment with specified packages
  - convert_environment: Convert an Anaconda environment to a conda-forge environment
  - convert_multiple_environments: Convert multiple environments in batch mode

The module also defines several exception types for handling errors during
the conversion process, such as ConversionError, EnvironmentCreationError,
and PackageInstallationError.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Annotated,
    Self,
    TypeAlias,
    TypedDict,
    cast,
)

from conda_forge_converter.utils import PathLike

# Import yaml with proper error handling
try:
    import yaml
    from yaml import YAMLError
except ImportError:
    raise ImportError(
        "PyYAML is required for this application. Please install it with: pip install pyyaml"
    ) from None

from .exceptions import (
    ConversionError,
    DiskSpaceError,
    EnvironmentCreationError,
    PackageInstallationError,
)
from .utils import (
    check_disk_space as utils_check_disk_space,
)
from .utils import (
    is_command_output_str,
    is_conda_environment,
    logger,
    run_command,
)

# Re-export check_disk_space for easier mocking in tests
check_disk_space = utils_check_disk_space

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


def find_environments_in_path(  # noqa: C901
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

    def scan_directory(current_path: PathLike, current_depth: int) -> None:  # noqa: C901
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
    try:
        envs = list_all_conda_environments(verbose=verbose)
        return env_name in envs
    except Exception as e:
        logger.error(f"Error checking if environment exists: {e!s}")
        return False


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
    output = run_command([*base_cmd, "--from-history"], verbose)

    if is_command_output_str(output):
        try:
            env_yaml: EnvironmentYaml = yaml.safe_load(output)
            dependencies = env_yaml.get("dependencies", [])
            if dependencies:
                logger.debug(f"Successfully exported environment {env_identifier} with history")
                return dependencies, True
            logger.warning(f"Environment {env_identifier} has no dependencies in history")
        except YAMLError as e:
            logger.error(f"Error parsing YAML output from conda env export: {e!s}")

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
            logger.error(f"Error parsing YAML output from conda env export: {e!s}")
            raise RuntimeError(f"Failed to parse conda environment {env_identifier}: {e!s}") from e

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
                f"Environment '{env_name}' has {conda_count} conda packages "
                f"and {pip_count} pip packages"
            )

        # Rough estimate: 50MB per package on average
        return total_packages * 50
    except Exception as e:
        logger.error(f"Error estimating environment size: {e!s}")
        return 100  # Default guess if we can't parse


# === ENVIRONMENT CONVERSION FUNCTIONS ===


def create_conda_forge_environment(  # noqa: C901
    source_env: str,
    target_env: str,
    conda_packages: CondaPackages,
    pip_packages: PipPackages,
    python_version: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
    use_fast_solver: bool = True,
    batch_size: int = 20,
    preserve_ownership: bool = True,
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
        use_fast_solver: Whether to use faster conda solvers if available
        batch_size: Number of packages to install in each batch
        preserve_ownership: Wether conda forge environments should have the same owner as Anaconda when running as root

    Returns:
        True if the operation succeeded, False otherwise

    """  # noqa: E501
    # Store original ownership information if running as root and preservation is enabled
    source_uid = None
    source_gid = None
    running_as_root = False

    try:
        from .utils import change_path_owner, get_owner_names, get_path_owner, is_root

        running_as_root = is_root()

        if running_as_root and preserve_ownership:
            # Get environments to find the path of the source environment
            environments = list_all_conda_environments(verbose=verbose)
            if source_env in environments:
                source_path = environments[source_env]
                try:
                    source_uid, source_gid = get_path_owner(source_path)
                    username, groupname = get_owner_names(source_uid, source_gid)
                    logger.info(
                        f"Source environment owned by {username}:{groupname} "
                        f"(UID={source_uid}, GID={source_gid})"
                    )
                except Exception as e:
                    logger.warning(f"Could not determine ownership of source environment: {e!s}")
                    logger.warning("Will not preserve ownership")
    except ImportError:
        logger.warning("Could not import ownership management functions")

    if dry_run:
        # Log what would be created
        logger.info(f"Would create conda-forge environment: {target_env}")
        logger.info(f"Based on: {source_env}")

        if running_as_root and preserve_ownership and source_uid is not None:
            logger.info("Would preserve ownership from source environment")

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

    # Determine which solver to use
    solver_args = []
    if use_fast_solver:
        # Try libmamba solver first, fall back to default if not available
        try:
            # Check if libmamba solver is available
            result = run_command(["conda", "config", "--show", "solver"], verbose=False)
            if is_command_output_str(result) and "libmamba" in result:
                solver_args = ["--solver=libmamba"]
                logger.info("Using libmamba solver for faster dependency resolution")
            else:
                # Try to see if mamba is installed
                mamba_result = run_command(["which", "mamba"], verbose=False)
                if is_command_output_str(mamba_result) and "mamba" in mamba_result:
                    # Use mamba instead of conda for faster operations
                    logger.info("Using mamba for faster dependency resolution")
                    # We'll handle this in the individual functions
                else:
                    logger.warning("Fast solvers not available, using default conda solver")
        except Exception as e:
            logger.warning(f"Error checking for fast solvers: {e!s}")
            logger.warning("Using default conda solver")

    # 1. Create base environment with Python
    if _create_base_environment(target_env, python_version, verbose, solver_args) is False:
        return False

    # 2. Install conda packages
    if conda_packages and not _install_conda_packages_in_batches(
        target_env, conda_packages, batch_size, verbose, solver_args
    ):
        return False

    # 3. Install pip packages
    if pip_packages and not _install_pip_packages_in_batches(
        target_env, pip_packages, batch_size, verbose
    ):
        return False

    # After successful environment creation, change ownership if running as root
    # and preservation is enabled
    if running_as_root and preserve_ownership and source_uid is not None and source_gid is not None:
        try:
            # Get the path of the newly created environment
            environments = list_all_conda_environments(verbose=verbose)
            if target_env in environments:
                target_path = environments[target_env]
                logger.info(f"Changing ownership of {target_path} to match source environment")
                # Use try-except to handle potential NameError
                try:
                    if change_path_owner(target_path, source_uid, source_gid):  # pyright: ignore[reportPossiblyUnboundVariable]
                        logger.info("Successfully changed ownership")
                    else:
                        logger.warning("Failed to change ownership")
                except NameError:
                    logger.warning("change_path_owner function not available")
        except Exception as e:
            logger.warning(f"Error changing ownership: {e!s}")

    logger.info(f"Successfully created conda-forge environment '{target_env}'")
    return True


def _create_base_environment(
    target_env: str, python_version: str | None, verbose: bool, solver_args: list[str] | None = None
) -> bool:
    """Create a base conda environment with the specified Python version.

    Args:
    ----
        target_env: Name of the target environment
        python_version: Python version to use
        verbose: Whether to log detailed information
        solver_args: Additional arguments for the mamba solver

    Returns:
    -------
        True if successful, False otherwise

    Raises:
    ------
        EnvironmentCreationError: If the environment cannot be created

    """
    try:
        python_spec = f"python={python_version}" if python_version else "python"

        # Initialize solver_args if None
        if solver_args is None:
            solver_args = []

        # Check if mamba is available and we're using solver_args (indicating fast solver requested)
        use_mamba = False
        if solver_args:
            mamba_result = run_command(["which", "mamba"], verbose=False)
            use_mamba = is_command_output_str(mamba_result) and "mamba" in mamba_result

        if use_mamba:
            cmd = ["mamba", "create", "-n", target_env, "-c", "conda-forge", python_spec, "-y"]
            logger.info("Using mamba to create environment")
        else:
            cmd = [
                "conda",
                "create",
                "-n",
                target_env,
                "-c",
                "conda-forge",
                python_spec,
                "-y",
            ]
            if solver_args:
                cmd.extend(solver_args)

        result = run_command(cmd, verbose)
        if not is_command_output_str(result):
            logger.error(f"Failed to create environment '{target_env}'")
            return False
        return True
    except Exception as e:
        error_msg = f"Failed to create base environment: {e!s}"
        logger.error(error_msg)
        raise EnvironmentCreationError(target_env, str(e)) from e


def _install_conda_packages_in_batches(  # noqa: C901
    target_env: str,
    conda_packages: CondaPackages,
    batch_size: int = 20,
    verbose: bool = False,
    solver_args: list[str] | None = None,
) -> bool:
    """Install conda packages in batches to improve performance.

    Args:
    ----
        target_env: Name of the target environment
        conda_packages: List of conda packages to install
        batch_size: Number of packages to install in each batch
        verbose: Whether to log detailed information
        solver_args: Additional arguments for the conda solver

    Returns:
    -------
        True if successful, False otherwise

    Raises:
    ------
        PackageInstallationError: If packages cannot be installed
    """
    if not conda_packages:
        return True

    try:
        # Format package specifications
        package_specs = []
        for pkg in conda_packages:
            if pkg["version"]:
                package_specs.append(f"{pkg['name']}={pkg['version']}")
            else:
                package_specs.append(pkg["name"])

        # Initialize solver_args if None
        if solver_args is None:
            solver_args = []

        # Check if mamba is available and we're using solver_args (indicating fast solver requested)
        use_mamba = False
        if solver_args:
            mamba_result = run_command(["which", "mamba"], verbose=False)
            use_mamba = is_command_output_str(mamba_result) and "mamba" in mamba_result

        # Split into batches
        batches = [
            package_specs[i : i + batch_size] for i in range(0, len(package_specs), batch_size)
        ]
        logger.info(f"Installing {len(package_specs)} conda packages in {len(batches)} batches")

        # Install each batch
        for i, batch in enumerate(batches):
            logger.info(f"Installing batch {i + 1}/{len(batches)} ({len(batch)} packages)")

            if use_mamba:
                cmd = ["mamba", "install", "-n", target_env, "-c", "conda-forge", "-y"]
                cmd.extend(batch)
                logger.debug("Using mamba for package installation")
            else:
                cmd = ["conda", "install", "-n", target_env, "-c", "conda-forge", "-y"]
                cmd.extend(solver_args)
                cmd.extend(batch)

            result = run_command(cmd, verbose=verbose)
            if not is_command_output_str(result):
                # If batch install fails, try installing packages one by one
                logger.warning("Batch installation failed, trying individual installations")
                for pkg_spec in batch:
                    if use_mamba:
                        cmd = [
                            "mamba",
                            "install",
                            "-n",
                            target_env,
                            "-c",
                            "conda-forge",
                            "-y",
                            pkg_spec,
                        ]
                    else:
                        cmd = ["conda", "install", "-n", target_env, "-c", "conda-forge", "-y"]
                        cmd.extend(solver_args)
                        cmd.append(pkg_spec)

                    result = run_command(cmd, verbose=verbose)
                    if not is_command_output_str(result):
                        logger.error(f"Failed to install {pkg_spec}")
                        return False

        return True
    except Exception as e:
        error_msg = f"Failed to install conda packages: {e!s}"
        logger.error(error_msg)
        raise PackageInstallationError(
            ", ".join([pkg["name"] for pkg in conda_packages]), str(e)
        ) from e


def _install_conda_packages(target_env: str, conda_packages: CondaPackages, verbose: bool) -> bool:
    """Legacy method for installing conda packages (for backward compatibility).

    This method is kept for backward compatibility but delegates to the batched version.
    """
    return _install_conda_packages_in_batches(
        target_env, conda_packages, batch_size=len(conda_packages), verbose=verbose
    )


def _install_pip_packages_in_batches(
    target_env: str, pip_packages: PipPackages, batch_size: int = 20, verbose: bool = False
) -> bool:
    """Install pip packages in batches to improve performance.

    Args:
    ----
        target_env: Name of the target environment
        pip_packages: List of pip packages to install
        batch_size: Number of packages to install in each batch
        verbose: Whether to log detailed information

    Returns:
    -------
        True if successful, False otherwise

    Raises:
    ------
        PackageInstallationError: If a package cannot be installed

    """
    if not pip_packages:
        return True

    try:
        # Format package specifications
        package_specs = []
        for pkg in pip_packages:
            if pkg["version"]:
                package_specs.append(f"{pkg['name']}=={pkg['version']}")
            else:
                package_specs.append(pkg["name"])

        # Split into batches
        batches = [
            package_specs[i : i + batch_size] for i in range(0, len(package_specs), batch_size)
        ]
        logger.info(f"Installing {len(package_specs)} pip packages in {len(batches)} batches")

        # Install each batch
        for i, batch in enumerate(batches):
            logger.info(f"Installing pip batch {i + 1}/{len(batches)} ({len(batch)} packages)")

            cmd = [*["conda", "run", "-n", target_env, "pip", "install"], *batch]
            result = run_command(cmd, verbose=verbose)
            if not is_command_output_str(result):
                # If batch install fails, try installing packages one by one
                logger.warning("Pip batch installation failed, trying individual installations")
                for pkg_spec in batch:
                    cmd = ["conda", "run", "-n", target_env, "pip", "install", pkg_spec]
                    result = run_command(cmd, verbose=verbose)
                    if not is_command_output_str(result):
                        logger.error(f"Failed to install pip package {pkg_spec}")
                        return False

        return True
    except Exception as e:
        error_msg = f"Failed to install pip packages: {e!s}"
        logger.error(error_msg)
        raise PackageInstallationError(
            ", ".join([pkg["name"] for pkg in pip_packages]), str(e)
        ) from e


def _install_pip_packages(target_env: str, pip_packages: PipPackages, verbose: bool) -> bool:
    """Legacy method for installing pip packages (for backward compatibility).

    This method is kept for backward compatibility but delegates to the batched version.
    """
    return _install_pip_packages_in_batches(
        target_env, pip_packages, batch_size=len(pip_packages), verbose=verbose
    )


def _raise_conversion_error(source_env: str, target_env: str, message: str) -> None:
    """Raise a conversion error."""
    raise ConversionError(source_env, target_env, message)


def get_environment_info(env_name: str, verbose: bool = False) -> EnvironmentInfo | None:
    """Get information about an environment.

    Args:
        env_name: Name of the environment
        verbose: Whether to print verbose output

    Returns:
        EnvironmentInfo object if successful, None otherwise

    """
    try:
        env_info = EnvironmentInfo.from_environment(env_name, "", verbose)
        if (
            not env_info
            or not hasattr(env_info, "conda_packages")
            or not hasattr(env_info, "pip_packages")
        ):
            logger.error(f"Invalid environment info for '{env_name}'")
            return None
        return env_info
    except Exception as e:
        logger.error(f"Error getting environment info: {e!s}")
        return None


def convert_environment(  # noqa: C901
    source_env: str,
    target_env: str | None = None,
    python_version: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
    use_fast_solver: bool = True,
    batch_size: int = 20,
    preserve_ownership: bool = True,
    replace_original: bool = True,
    backup_suffix: str = "_anaconda_backup",
) -> bool:
    """Convert a conda environment to use conda-forge packages.

    Args:
        source_env: Name of the source environment
        target_env: Name of the target environment (if None and replace_original is False, will use source_env + "_forge")
        python_version: Python version to use (default: same as source)
        dry_run: If True, only simulate the operation
        verbose: Whether to print verbose output
        use_fast_solver: Whether to use faster conda solvers if available
        batch_size: Number of packages to install in each batch
        preserve_ownership: Whether to preserve the ownership of the source environment
        replace_original: Whether to replace the original environment (default: True)
        backup_suffix: Suffix to add to the backup environment name

    Returns:
        True if conversion was successful, False otherwise

    """  # noqa: E501
    try:
        # Check if source environment exists
        if not environment_exists(source_env, verbose):
            logger.error(f"Source environment '{source_env}' does not exist")
            return False

        # Determine target environment name
        if replace_original:
            # If replacing original, target is the same as source
            effective_target = source_env

            # Backup the original environment
            if not dry_run:
                if not backup_environment(source_env, backup_suffix, verbose):
                    logger.error(f"Failed to backup environment '{source_env}'")
                    return False

                # Remove the original environment
                logger.info(f"Removing original environment '{source_env}'...")
                result = run_command(["conda", "env", "remove", "--name", source_env], verbose)
                if not is_command_output_str(result):
                    logger.error(f"Failed to remove original environment '{source_env}'")
                    return False
        else:
            # If not replacing, use provided target or default
            effective_target = target_env or f"{source_env}_forge"

            # Check if target environment already exists
            if environment_exists(effective_target, verbose):
                logger.error(f"Target environment '{effective_target}' already exists")
                return False

        # Get environment info
        env_info = EnvironmentInfo.from_environment(source_env, "", verbose)
        if not env_info:
            raise ConversionError(source_env, effective_target, "Failed to analyze environment")

        # Create conda-forge environment
        conda_packages = getattr(env_info, "conda_packages", [])
        pip_packages = getattr(env_info, "pip_packages", [])
        python_ver = python_version or getattr(env_info, "python_version", None)

        result = create_conda_forge_environment(
            source_env,
            effective_target,
            conda_packages,
            pip_packages,
            python_ver,
            dry_run,
            verbose,
            use_fast_solver=use_fast_solver,
            batch_size=batch_size,
            preserve_ownership=preserve_ownership,
        )

        if result:
            if replace_original:
                logger.info(
                    f"Successfully replaced environment '{source_env}' with conda-forge packages"
                )
                logger.info(f"Original environment backed up as '{source_env}{backup_suffix}'")
            else:
                logger.info(
                    f"Successfully converted environment '{source_env}' to '{effective_target}'"
                )

        return result

    except (EnvironmentCreationError, PackageInstallationError) as e:
        raise ConversionError(source_env, effective_target, str(e)) from e
    except Exception as e:
        raise ConversionError(source_env, effective_target, f"Unexpected error: {e!s}") from e


def _raise_disk_space_error(required: int, free: int) -> None:
    """Raise a disk space error."""
    raise DiskSpaceError(required, free)


def convert_multiple_environments(  # noqa: C901
    source_envs: list[str] | None = None,
    target_envs: list[str] | None = None,
    python_version: str | None = None,
    env_pattern: str | None = None,
    exclude: str | None = None,
    target_suffix: str = "_forge",
    dry_run: bool = False,
    verbose: bool = False,
    max_parallel: int = 1,
    backup: bool = False,
    search_paths: list[str | Path] | None = None,
    use_fast_solver: bool = True,
    batch_size: int = 20,
    preserve_ownership: bool = True,
    replace_original: bool = True,
    backup_suffix: str = "_anaconda_backup",
) -> bool:
    """Convert multiple conda environments to use conda-forge packages.

    Args:
        source_envs: List of source environment names (if None, will find all environments)
        target_envs: List of target environment names (default: source_envs + target_suffix)
        python_version: Python version to use (default: same as source)
        env_pattern: Pattern to filter environment names (e.g., "data*")
        exclude: Pattern to exclude environment names (e.g., "base,*test*")
        target_suffix: Suffix to add to source environment names for targets (default: "_forge")
        dry_run: If True, only simulate the operation
        verbose: Whether to print verbose output
        max_parallel: Maximum number of parallel conversions (default: 1)
        backup: Whether to backup environments before conversion
        search_paths: Additional paths to search for environments
        use_fast_solver: Whether to use faster conda solvers if available
        batch_size: Number of packages to install in each batch
        preserve_ownership: Whether to preserve the ownership of the source environments
        replace_original: Whether to replace the original environments (default: True)
        backup_suffix: Suffix to add to the backup environment name

    Returns:
        True if all conversions were successful, False otherwise

    """
    # Find all conda environments if source_envs not provided
    if source_envs is None:
        # Convert search_paths to the expected type if needed
        path_list: list[PathLike] | None = None
        if search_paths:
            path_list = search_paths  # search_paths is already list[str | Path]
        all_envs = list_all_conda_environments(path_list, verbose)
        if not all_envs:
            logger.error("No conda environments found")
            return False

        source_envs = list(all_envs.keys())

        # Filter environments by pattern if provided
        if env_pattern:
            import fnmatch

            source_envs = [env for env in source_envs if fnmatch.fnmatch(env, env_pattern)]

        # Exclude environments by pattern if provided
        if exclude:
            import fnmatch

            exclude_patterns = exclude.split(",")
            for pattern in exclude_patterns:
                source_envs = [
                    env for env in source_envs if not fnmatch.fnmatch(env, pattern.strip())
                ]

        if not source_envs:
            logger.warning("No environments found matching the criteria")
            return False

        logger.info(f"Found {len(source_envs)} environments to convert")

    # Determine target environment names if not provided
    if target_envs is None:
        if replace_original:
            # If replacing original, target names are the same as source names
            target_envs = source_envs
        else:
            # If not replacing, add suffix to source names
            target_envs = [f"{env}{target_suffix}" for env in source_envs]

    # Check disk space if needed
    if not dry_run and max_parallel > 0:
        # Estimate required space (rough estimate)
        try:
            if not check_disk_space(5 * len(source_envs)):  # Assume 5GB per environment
                logger.warning("Low disk space detected. Conversion may fail.")
        except Exception as e:
            logger.warning(f"Could not check disk space: {e!s}")

    # Track results
    results = {}
    successful = 0
    failed = 0
    skipped = 0

    # Convert each environment
    for source_env, target_env in zip(source_envs, target_envs, strict=False):
        try:
            result = convert_environment(
                source_env,
                target_env if not replace_original else None,
                python_version,
                dry_run,
                verbose,
                use_fast_solver=use_fast_solver,
                batch_size=batch_size,
                preserve_ownership=preserve_ownership,
                replace_original=replace_original,
                backup_suffix=backup_suffix,
            )
            results[source_env] = result
            if result:
                successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Error converting environment '{source_env}': {e!s}")
            results[source_env] = False
            failed += 1

    # Log summary
    logger.info("========================================")
    logger.info("Conversion Summary:")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Skipped: {skipped}")
    logger.info("========================================")

    return failed == 0 and successful > 0


# This function is imported from utils, so we don't need to redefine it here


def backup_environment(
    env_name: str, backup_suffix: str = "_anaconda_backup", verbose: bool = False
) -> bool:
    """Backup a conda environment with a temporary name.

    Args:
        env_name: Name of the environment to backup
        backup_suffix: Suffix to add to the backup environment name
        verbose: Whether to log detailed information

    Returns:
        True if successful, False otherwise
    """
    backup_name = f"{env_name}{backup_suffix}"

    # Check if backup already exists
    if environment_exists(backup_name, verbose):
        logger.info(f"Backup environment '{backup_name}' already exists, removing it...")
        # Remove existing backup
        result = run_command(["conda", "env", "remove", "--name", backup_name], verbose)
        if not is_command_output_str(result):
            logger.error(f"Failed to remove existing backup environment '{backup_name}'")
            return False

    # Clone the environment to create a backup
    logger.info(f"Backing up environment '{env_name}' to '{backup_name}'...")
    result = run_command(
        ["conda", "create", "--name", backup_name, "--clone", env_name, "-y"], verbose
    )
    if not is_command_output_str(result):
        logger.error(f"Failed to backup environment '{env_name}'")
        return False

    logger.info(f"Successfully backed up environment '{env_name}' to '{backup_name}'")
    return True


# This function is imported from utils, so we don't need to redefine it here
