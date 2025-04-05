"""Core functionality for the conda-forge-converter package."""

import datetime
import fnmatch
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import (
    Any, Literal, Protocol, TypeAlias, TypedDict, TypeVar, cast,
    Annotated, Self, NotRequired, get_origin, get_args
)

import yaml

from .utils import (
    check_disk_space, is_conda_environment, is_command_output_str,
    logger, run_command, PathLike
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
    failed: list[tuple[str, str]]   # (source_env, reason)
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
            name: Name of the environment
            path: Path to the environment
            verbose: Whether to log detailed information
            
        Returns:
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

def find_environments_in_path(search_path: PathLike, max_depth: int = 3, verbose: bool = False) -> EnvMapping:
    """Find conda environments in a directory tree.
    
    Args:
        search_path: Root path to search for environments
        max_depth: Maximum directory depth to search
        verbose: Whether to log detailed information
        
    Returns:
        Dictionary mapping environment names to their paths
    """
    if not os.path.exists(search_path):
        logger.warning(f"Search path does not exist: {search_path}")
        return {}
    
    found_envs: EnvMapping = {}
    
    def scan_directory(current_path: PathLike, current_depth: int) -> None:
        if current_depth > max_depth:
            return
        
        try:
            if is_conda_environment(current_path):
                # Use the directory name as the environment name
                env_name = os.path.basename(current_path)
                found_envs[env_name] = str(current_path)
                # Don't need to go deeper if this is an environment
                return
            
            # Scan subdirectories
            try:
                subdirs = [os.path.join(current_path, d) for d in os.listdir(current_path) 
                         if os.path.isdir(os.path.join(current_path, d))]
                
                for subdir in subdirs:
                    scan_directory(subdir, current_depth + 1)
            except (PermissionError, OSError):
                if verbose:
                    logger.debug(f"Skipping directory due to permission error: {current_path}")
        except (PermissionError, OSError):
            if verbose:
                logger.debug(f"Skipping directory due to permission error: {current_path}")
    
    # Start scanning
    scan_directory(search_path, 0)
    
    if verbose and found_envs:
        logger.info(f"Found {len(found_envs)} conda environments in {search_path}")
    
    return found_envs


def list_all_conda_environments(search_paths: list[PathLike] | None = None, verbose: bool = False) -> EnvMapping:
    """List all conda environments on the system and in specified search paths.
    
    Args:
        search_paths: Additional paths to search for environments
        verbose: Whether to log detailed information
        
    Returns:
        Dictionary mapping environment names to their paths
    """
    env_dict: EnvMapping = {}
    
    # Get registered environments through conda command
    output = run_command(["conda", "env", "list", "--json"], verbose)
    if is_command_output_str(output):
        try:
            env_data = json.loads(output)
            for env_path in env_data.get("envs", []):
                # The base environment is a special case
                if os.path.basename(os.path.dirname(env_path)) in ["anaconda3", "miniconda3"] and os.path.basename(env_path) == "envs":
                    env_name = "base"
                else:
                    env_name = os.path.basename(env_path)
                
                env_dict[env_name] = env_path
                
            if verbose:
                logger.info(f"Found {len(env_dict)} registered conda environments")
        except json.JSONDecodeError:
            logger.error("Error parsing JSON output from conda env list")
    
    # Search for additional environments in specified paths
    if search_paths:
        for path in search_paths:
            found_envs = find_environments_in_path(path, verbose=verbose)
            for env_name, env_path in found_envs.items():
                # Avoid duplicates, but note conflicts
                if env_name in env_dict and env_dict[env_name] != env_path:
                    # There's already an environment with this name but different path
                    # Append a suffix to make it unique
                    base_name = env_name
                    counter = 1
                    while env_name in env_dict:
                        env_name = f"{base_name}_{counter}"
                        counter += 1
                    if verbose:
                        logger.info(f"Renamed environment to avoid conflict: {base_name} → {env_name}")
                
                env_dict[env_name] = env_path
    
    return env_dict


def environment_exists(env_name: str, verbose: bool = False) -> bool:
    """Check if a conda environment exists.
    
    Args:
        env_name: Name of the environment to check
        verbose: Whether to log detailed information
        
    Returns:
        True if the environment exists, False otherwise
    """
    env_dict = list_all_conda_environments(verbose=verbose)
    return env_name in env_dict


# === ENVIRONMENT ANALYSIS FUNCTIONS ===

def get_python_version(env_name: str, env_path: PathLike | None = None, verbose: bool = False) -> str | None:
    """Get the Python version in the specified environment.
    
    Args:
        env_name: Name of the environment
        env_path: Path to the environment (if known)
        verbose: Whether to log detailed information
        
    Returns:
        Python version string or None if it couldn't be determined
    """
    if env_path:
        # Use --prefix for custom environments
        output = run_command(
            ["conda", "list", "--prefix", str(env_path), "python", "--json"],
            verbose
        )
    else:
        # Use --name for registered environments
        output = run_command(
            ["conda", "list", "--name", env_name, "python", "--json"],
            verbose
        )
    
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


def get_environment_packages(env_name: str, env_path: PathLike | None = None, 
                          verbose: bool = False) -> tuple[list[Any], bool]:
    """Get packages that were explicitly installed by the user.
    
    Args:
        env_name: Name of the environment
        env_path: Path to the environment (if known)
        verbose: Whether to log detailed information
        
    Returns:
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
    output = run_command(
        base_cmd + ["--from-history"],
        verbose
    )
    
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
    
    output = run_command(
        base_cmd,
        verbose
    )
    
    if is_command_output_str(output):
        try:
            env_yaml = yaml.safe_load(output)
            return env_yaml.get("dependencies", []), False
        except yaml.YAMLError:
            logger.error("Error parsing YAML output from conda env export")
    
    return [], False


def extract_package_specs(dependencies: list[Any]) -> tuple[CondaPackages, PipPackages]:
    """Extract package specifications from the dependencies list.
    
    Args:
        dependencies: List of dependency specifications from conda env export
        
    Returns:
        Tuple of (conda_packages, pip_packages)
    """
    conda_packages: CondaPackages = []
    pip_packages: PipPackages = []
    
    for dep in dependencies:
        if isinstance(dep, str):
            # Handle conda packages (format: 'package=version' or just 'package')
            if dep != "pip" and not dep.startswith("python="):  # Skip 'pip' and 'python=' entries
                parts = dep.split('=')
                name = parts[0]
                version = parts[1] if len(parts) > 1 else None
                conda_packages.append({"name": name, "version": version})
        elif isinstance(dep, dict) and "pip" in dep:
            # Handle pip packages
            for pip_dep in dep["pip"]:
                parts = pip_dep.split('==')
                name = parts[0]
                version = parts[1] if len(parts) > 1 else None
                pip_packages.append({"name": name, "version": version})
    
    return conda_packages, pip_packages


def get_environment_size(env_name: str, verbose: bool = False) -> int:
    """Estimate the size of an environment in MB.
    
    Args:
        env_name: Name of the environment
        verbose: Whether to log detailed information
        
    Returns:
        Estimated size in megabytes
    """
    output = run_command(
        ["conda", "env", "export", "--name", env_name],
        verbose
    )
    
    if not is_command_output_str(output):
        return 0
    
    # Crude estimation based on the number of packages
    try:
        env_yaml = yaml.safe_load(output)
        dependencies = env_yaml.get("dependencies", [])
        
        # Count pip packages
        pip_count = 0
        for dep in dependencies:
            if isinstance(dep, dict) and "pip" in dep:
                pip_count += len(dep["pip"])
                
        # Count conda packages
        conda_count = sum(1 for dep in dependencies if isinstance(dep, str))
        
        # Rough estimate: 50MB per package on average
        return (conda_count + pip_count) * 50
    except:
        return 100  # Default guess if we can't parse


# === ENVIRONMENT CONVERSION FUNCTIONS ===

def create_conda_forge_environment(source_env: str, target_env: str, 
                                 conda_packages: CondaPackages, 
                                 pip_packages: PipPackages, 
                                 python_version: str | None = None, 
                                 dry_run: bool = False, 
                                 verbose: bool = False) -> bool:
    """Create a new environment with conda-forge and install the same packages.
    
    Args:
        source_env: Name of the source environment
        target_env: Name of the target environment
        conda_packages: List of conda packages to install
        pip_packages: List of pip packages to install
        python_version: Python version to use
        dry_run: Whether to simulate the operation
        verbose: Whether to log detailed information
        
    Returns:
        True if the operation succeeded, False otherwise
    """
    if dry_run:
        # Using logger.info for dry-run output for consistency
        logger.info(f"DRY RUN: Would create conda-forge environment '{target_env}' based on '{source_env}'")
        
        if python_version:
            logger.info(f"  Python version: {python_version}")
        
        if conda_packages:
            logger.info(f"  Conda packages to install: {len(conda_packages)}")
            for pkg in conda_packages[:5]:  # Show just a few for brevity
                if pkg["version"]:
                    logger.info(f"    - {pkg['name']}={pkg['version']}")
                else:
                    logger.info(f"    - {pkg['name']}")
            if len(conda_packages) > 5:
                logger.info(f"    - ... and {len(conda_packages) - 5} more")
        
        if pip_packages:
            logger.info(f"  Pip packages to install: {len(pip_packages)}")
            for pkg in pip_packages[:5]:  # Show just a few
                if pkg["version"]:
                    logger.info(f"    - {pkg['name']}=={pkg['version']}")
                else:
                    logger.info(f"    - {pkg['name']}")
            if len(pip_packages) > 5:
                logger.info(f"    - ... and {len(pip_packages) - 5} more")
        return True
    
    # Create new environment with the same Python version if specified
    logger.info(f"Creating new environment '{target_env}'...")
    create_cmd = ["conda", "create", "--name", target_env, "--yes", "-c", "conda-forge"]
    
    if python_version:
        create_cmd.append(f"python={python_version}")
    else:
        create_cmd.append("python")
        
    if not run_command(create_cmd, verbose):
        logger.error(f"Failed to create environment '{target_env}'")
        return False
    
    success = True
    
    if conda_packages:
        # Prepare package specifications
        package_specs: list[str] = []
        for pkg in conda_packages:
            if pkg["version"]:
                package_specs.append(f"{pkg['name']}={pkg['version']}")
            else:
                package_specs.append(pkg["name"])
        
        # Install conda packages from conda-forge
        logger.info(f"Installing conda packages from conda-forge in '{target_env}'...")
        install_cmd = ["conda", "install", "--name", target_env, "--yes", "-c", "conda-forge"] + package_specs
        
        if not run_command(install_cmd, verbose):
            logger.warning("Some conda packages failed to install")
            success = False
    else:
        logger.info("No conda packages to install")
        
    if pip_packages:
        # Install pip first if needed
        run_command(["conda", "install", "--name", target_env, "--yes", "-c", "conda-forge", "pip"], verbose)
        
        # Prepare pip package specifications
        pip_specs: list[str] = []
        for pkg in pip_packages:
            if pkg["version"]:
                pip_specs.append(f"{pkg['name']}=={pkg['version']}")
            else:
                pip_specs.append(pkg["name"])
        
        # Install pip packages
        logger.info(f"Installing pip packages in '{target_env}'...")
        pip_cmd = ["conda", "run", "--name", target_env, "pip", "install"] + pip_specs
        
        if not run_command(pip_cmd, verbose):
            logger.warning("Some pip packages failed to install")
            success = False
    else:
        logger.info("No pip packages to install")
    
    if success:
        logger.info(f"Successfully created conda-forge environment '{target_env}' based on '{source_env}'")
    else:
        logger.warning(f"Environment '{target_env}' was created, but some packages failed to install")
        logger.warning("Check the output above for details")
    
    return success


def convert_environment(source_env: str, target_env: str | None = None, 
                      python_version: str | None = None, dry_run: bool = False, 
                      verbose: bool = False, env_path: PathLike | None = None) -> bool:
    """Convert a single environment from Anaconda to conda-forge.
    
    Args:
        source_env: Name of the source environment
        target_env: Name of the target environment
        python_version: Python version to use
        dry_run: Whether to simulate the operation
        verbose: Whether to log detailed information
        env_path: Path to the source environment
        
    Returns:
        True if the operation succeeded, False otherwise
    """
    if not target_env:
        target_env = f"{source_env}_forge"
    
    if environment_exists(target_env, verbose) and not dry_run:
        logger.warning(f"Target environment '{target_env}' already exists. Skipping conversion.")
        return False
    
    # Try to create an EnvironmentInfo
    env_info = EnvironmentInfo.from_environment(source_env, str(env_path) if env_path else source_env, verbose)
    if not env_info:
        logger.error(f"Could not determine packages for '{source_env}'. Skipping conversion.")
        return False
    
    # Use provided Python version if specified, otherwise use the detected one
    if python_version:
        env_info.python_version = python_version
        
    if verbose:
        source_type = "top-level" if env_info.conda_packages else "all"
        logger.info(f"Found {len(env_info.conda_packages)} {source_type} conda packages and "
                   f"{len(env_info.pip_packages)} {source_type} pip packages in '{source_env}'")
    
    # Create new environment
    return create_conda_forge_environment(
        source_env, 
        target_env, 
        env_info.conda_packages, 
        env_info.pip_packages, 
        env_info.python_version, 
        dry_run,
        verbose
    )


def convert_multiple_environments(env_pattern: str | None = None, 
                               target_suffix: str = "_forge", 
                               dry_run: bool = False, 
                               verbose: bool = False, 
                               exclude: str | None = None, 
                               max_parallel: int = 1, 
                               backup: bool = True, 
                               search_paths: list[PathLike] | None = None) -> bool:
    """Convert multiple environments matching a pattern.
    
    Args:
        env_pattern: Pattern to match environment names
        target_suffix: Suffix to add to target environment names
        dry_run: Whether to simulate the operation
        verbose: Whether to log detailed information
        exclude: Comma-separated list of environments to exclude
        max_parallel: Maximum number of parallel conversions
        backup: Whether to backup environment specifications
        search_paths: Additional paths to search for environments
        
    Returns:
        True if all operations succeeded, False otherwise
    """
    # Find all environments
    env_dict = list_all_conda_environments(search_paths=search_paths, verbose=verbose)
    if not env_dict:
        logger.error("No conda environments found")
        return False
    
    all_envs = list(env_dict.keys())
    logger.info(f"Found {len(all_envs)} conda environments: {', '.join(all_envs)}")
    
    # Filter environments based on pattern
    if env_pattern:
        envs_to_convert = [env for env in all_envs if fnmatch.fnmatch(env, env_pattern)]
    else:
        envs_to_convert = all_envs.copy()
    
    # Apply exclusions
    if exclude:
        exclude_list = exclude.split(',')
        envs_to_convert = [env for env in envs_to_convert if env not in exclude_list]
    
    if not envs_to_convert:
        logger.warning("No environments match the specified pattern and exclusions")
        return False
    
    logger.info(f"Will convert {len(envs_to_convert)} environments: {', '.join(envs_to_convert)}")
    
    # Estimate disk space needed
    if not dry_run:
        total_size_mb = 0
        for env in envs_to_convert:
            size_mb = get_environment_size(env, verbose)
            total_size_mb += size_mb
            if verbose:
                logger.debug(f"Estimated size of '{env}': {size_mb} MB")
        
        total_size_gb = total_size_mb / 1024  # Convert to GB
        logger.info(f"Estimated total disk space needed: {total_size_gb:.1f} GB")
        
        # Check if we have enough space
        if not check_disk_space(needed_gb=total_size_gb * 1.2):  # Add 20% buffer
            if not dry_run:
                # This input is intentionally kept for user interaction
                response = input("Disk space may be insufficient. Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    logger.warning("Conversion aborted due to insufficient disk space")
                    return False
    
    # Create backup directory
    backup_dir = None
    if backup and not dry_run:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"conda_env_backups_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Created backup directory: {backup_dir}")
    
    results: ConversionResults = {"success": [], "failed": [], "skipped": []}
    
    def process_environment(source_env: str) -> None:
        target_env = f"{source_env}{target_suffix}"
        env_path = env_dict.get(source_env)
        
        # Skip if target already exists
        if environment_exists(target_env, verbose) and not dry_run:
            logger.warning(f"Skipping {source_env}: Target environment {target_env} already exists")
            results["skipped"].append((source_env, "Target environment already exists"))
            return
        
        # Backup environment specification
        if backup_dir and not dry_run:
            backup_file = os.path.join(backup_dir, f"{source_env}_spec.yaml")
            if env_path:
                backup_cmd = ["conda", "env", "export", "--prefix", env_path, "--file", backup_file]
            else:
                backup_cmd = ["conda", "env", "export", "--name", source_env, "--file", backup_file]
                
            if not run_command(backup_cmd, verbose):
                logger.warning(f"Failed to backup environment {source_env}")
                # Continue anyway
        
        # Get Python version
        python_version = get_python_version(source_env, env_path, verbose)
        
        # Get package list
        dependencies, from_history = get_environment_packages(source_env, env_path, verbose)
        if not dependencies:
            logger.error(f"Could not determine packages for '{source_env}'. Skipping conversion.")
            results["failed"].append((source_env, "Could not determine packages"))
            return
            
        # Extract package specifications
        conda_packages, pip_packages = extract_package_specs(dependencies)
        
        # Display package info
        if verbose:
            source_type = "top-level" if from_history else "all"
            logger.info(f"Found {len(conda_packages)} {source_type} conda packages and "
                        f"{len(pip_packages)} {source_type} pip packages in '{source_env}'")
        
        # Log what we're about to do
        logger.info(f"Converting {source_env} to {target_env} with "
                   f"{len(conda_packages)} conda packages and {len(pip_packages)} pip packages")
        
        # Create new environment
        success = create_conda_forge_environment(
            source_env, 
            target_env, 
            conda_packages, 
            pip_packages, 
            python_version, 
            dry_run,
            verbose
        )
        
        if success:
            logger.info(f"Successfully converted {source_env} to {target_env}")
            results["success"].append((source_env, target_env))
        else:
            logger.error(f"Failed to convert {source_env}")
            results["failed"].append((source_env, "Conversion failed"))
    
    # Process environments (in parallel if requested)
    if max_parallel > 1 and not dry_run:
        logger.info(f"Converting environments using {max_parallel} parallel processes...")
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            list(executor.map(process_environment, envs_to_convert))
    else:
        for env in envs_to_convert:
            process_environment(env)
    
    # Generate summary report - using logger.info for consistent reporting
    logger.info("Conversion Summary:")
    logger.info(f"Successfully converted: {len(results['success'])}")
    for source, target in results['success']:
        logger.info(f"  - {source} → {target}")
    
    logger.info(f"Failed conversions: {len(results['failed'])}")
    for source, reason in results['failed']:
        logger.info(f"  - {source}: {reason}")
        
    logger.info(f"Skipped conversions: {len(results['skipped'])}")
    for source, reason in results['skipped']:
        logger.info(f"  - {source}: {reason}")
    
    logger.info(f"Conversion complete. Success: {len(results['success'])}, "
              f"Failed: {len(results['failed'])}, Skipped: {len(results['skipped'])}")
    
    return len(results["failed"]) == 0
