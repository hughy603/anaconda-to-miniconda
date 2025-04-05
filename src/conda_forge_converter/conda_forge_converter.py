#!/usr/bin/env python3
"""
conda-forge-converter.py - Convert Anaconda environments to conda-forge

This script converts one or multiple Anaconda environments to conda-forge environments
with the same top-level dependency versions. It can operate on a single environment
or batch convert all environments on a server.

Usage examples:
  # Convert a single environment
  python conda-forge-converter.py -s myenv -t myenv_forge
  
  # Batch convert all environments (adds _forge suffix by default)
  python conda-forge-converter.py --batch
  
  # Batch convert environments matching a pattern, excluding some
  python conda-forge-converter.py --batch --pattern "data*" --exclude "data_test,data_old"
  
  # Preview what would be converted without making changes
  python conda-forge-converter.py --batch --dry-run
  
  # Search for environments in custom paths
  python conda-forge-converter.py --batch --search-path /opt/conda_envs --search-path /home/user/envs
"""

import subprocess
import json
import argparse
import sys
import yaml
import os
import fnmatch
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor
import shutil
from typing import Dict, List, Tuple, Set, Any, Optional, TypedDict, Union


# =========== TYPE DEFINITIONS ===========

class CondaPackage(TypedDict):
    name: str
    version: Optional[str]


class PipPackage(TypedDict):
    name: str
    version: Optional[str]


class ConversionResults(TypedDict):
    success: List[Tuple[str, str]]
    failed: List[Tuple[str, str]]
    skipped: List[Tuple[str, str]]


# =========== LOGGING SETUP ===========

# Create a logger
logger = logging.getLogger('conda_converter')


def setup_logging(log_file: Optional[str] = None, verbose: bool = False) -> None:
    """Configure logging to file and console."""
    # Set the log level based on verbosity
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


# =========== UTILITY FUNCTIONS ===========

def run_command(cmd: List[str], verbose: bool = False, capture: bool = True) -> Optional[Union[str, bool]]:
    """Run a command and return its output, with optional verbose logging."""
    if verbose:
        logger.debug(f"Running: {' '.join(cmd)}")
    
    try:
        if capture:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        else:
            # Run without capturing output (for long-running commands)
            subprocess.run(cmd, check=True)
            return True
    except subprocess.CalledProcessError as e:
        if verbose or not capture:
            logger.error(f"Command failed with exit code {e.returncode}")
            logger.error(f"Command: {' '.join(cmd)}")
            if e.stdout:
                logger.error("STDOUT:")
                logger.error(e.stdout)
            if e.stderr:
                logger.error("STDERR:")
                logger.error(e.stderr)
        return None


def check_disk_space(needed_gb: float = 5, path: Optional[str] = None) -> bool:
    """Check if there's enough disk space available."""
    if path is None:
        path = os.getcwd()
    
    total, used, free = shutil.disk_usage(path)
    free_gb = free / (1024 ** 3)  # Convert to GB
    
    if free_gb < needed_gb:
        logger.warning(f"Only {free_gb:.1f} GB free space available. "
                      f"Recommended minimum: {needed_gb} GB")
        return False
    return True


# =========== ENVIRONMENT ANALYSIS FUNCTIONS ===========

def is_conda_environment(path: str) -> bool:
    """Check if a directory is a conda environment."""
    # A conda environment typically has these subdirectories
    conda_meta = os.path.join(path, "conda-meta")
    bin_dir = os.path.join(path, "bin") if not os.name == 'nt' else os.path.join(path, "Scripts")
    
    # Check for python executable
    python_exec = os.path.join(bin_dir, "python") if not os.name == 'nt' else os.path.join(path, "python.exe")
    
    # If conda-meta exists and either python or bin/Scripts exists, it's likely a conda env
    return (os.path.exists(conda_meta) and 
            (os.path.exists(python_exec) or os.path.exists(bin_dir)))


def find_environments_in_path(search_path: str, max_depth: int = 3, verbose: bool = False) -> Dict[str, str]:
    """Find conda environments in a directory tree."""
    if not os.path.exists(search_path):
        logger.warning(f"Search path does not exist: {search_path}")
        return {}
    
    found_envs: Dict[str, str] = {}
    
    def scan_directory(current_path: str, current_depth: int) -> None:
        if current_depth > max_depth:
            return
        
        try:
            if is_conda_environment(current_path):
                # Use the directory name as the environment name
                env_name = os.path.basename(current_path)
                found_envs[env_name] = current_path
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


def list_all_conda_environments(search_paths: Optional[List[str]] = None, verbose: bool = False) -> Dict[str, str]:
    """List all conda environments on the system and in specified search paths."""
    env_dict: Dict[str, str] = {}
    
    # Get registered environments through conda command
    output = run_command(["conda", "env", "list", "--json"], verbose)
    if output and isinstance(output, str):
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
                        logger.info(f"Renamed environment to avoid conflict: {base_name} -> {env_name}")
                
                env_dict[env_name] = env_path
    
    return env_dict


def get_python_version(env_name: str, env_path: Optional[str] = None, verbose: bool = False) -> Optional[str]:
    """Get the Python version in the specified environment."""
    if env_path:
        # Use --prefix for custom environments
        output = run_command(
            ["conda", "list", "--prefix", env_path, "python", "--json"],
            verbose
        )
    else:
        # Use --name for registered environments
        output = run_command(
            ["conda", "list", "--name", env_name, "python", "--json"],
            verbose
        )
    
    if not output or not isinstance(output, str):
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


def get_environment_packages(env_name: str, env_path: Optional[str] = None, 
                          verbose: bool = False) -> Tuple[List[Any], bool]:
    """Get packages that were explicitly installed by the user."""
    # Prepare base command based on whether we have a path or just a name
    if env_path:
        base_cmd = ["conda", "env", "export", "--prefix", env_path]
    else:
        base_cmd = ["conda", "env", "export", "--name", env_name]
    
    # Try with --from-history first
    output = run_command(
        base_cmd + ["--from-history"],
        verbose
    )
    
    if output and isinstance(output, str):
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
    
    if output and isinstance(output, str):
        try:
            env_yaml = yaml.safe_load(output)
            return env_yaml.get("dependencies", []), False
        except yaml.YAMLError:
            logger.error("Error parsing YAML output from conda env export")
    
    return [], False


def extract_package_specs(dependencies: List[Any]) -> Tuple[List[CondaPackage], List[PipPackage]]:
    """Extract package specifications from the dependencies list."""
    conda_packages: List[CondaPackage] = []
    pip_packages: List[PipPackage] = []
    
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


def environment_exists(env_name: str, verbose: bool = False) -> bool:
    """Check if a conda environment exists."""
    env_dict = list_all_conda_environments(verbose=verbose)
    return env_name in env_dict


def get_environment_size(env_name: str, verbose: bool = False) -> int:
    """Estimate the size of an environment in MB."""
    output = run_command(
        ["conda", "env", "export", "--name", env_name],
        verbose
    )
    
    if not output or not isinstance(output, str):
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


# =========== ENVIRONMENT CONVERSION FUNCTIONS ===========

def create_conda_forge_environment(source_env: str, target_env: str, 
                                 conda_packages: List[CondaPackage], 
                                 pip_packages: List[PipPackage], 
                                 python_version: Optional[str] = None, 
                                 dry_run: bool = False, 
                                 verbose: bool = False) -> bool:
    """Create a new environment with conda-forge and install the same packages."""
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
        package_specs: List[str] = []
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
        pip_specs: List[str] = []
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


def convert_environment(source_env: str, target_env: Optional[str] = None, 
                      python_version: Optional[str] = None, dry_run: bool = False, 
                      verbose: bool = False, env_path: Optional[str] = None) -> bool:
    """Convert a single environment from Anaconda to conda-forge."""
    if not target_env:
        target_env = f"{source_env}_forge"
    
    if environment_exists(target_env, verbose) and not dry_run:
        logger.warning(f"Target environment '{target_env}' already exists. Skipping conversion.")
        return False
    
    # Get Python version if not specified
    if not python_version:
        python_version = get_python_version(source_env, env_path, verbose)
        if python_version and verbose:
            logger.debug(f"Detected Python {python_version} in source environment")
    
    # Get package list
    dependencies, from_history = get_environment_packages(source_env, env_path, verbose)
    if not dependencies:
        logger.error(f"Could not determine packages for '{source_env}'. Skipping conversion.")
        return False
    
    # Extract package specifications
    conda_packages, pip_packages = extract_package_specs(dependencies)
    
    # Display package info
    if verbose:
        source_type = "top-level" if from_history else "all"
        logger.info(f"Found {len(conda_packages)} {source_type} conda packages and "
                   f"{len(pip_packages)} {source_type} pip packages in '{source_env}'")
    
    # Create new environment
    return create_conda_forge_environment(
        source_env, 
        target_env, 
        conda_packages, 
        pip_packages, 
        python_version, 
        dry_run,
        verbose
    )


def convert_multiple_environments(env_pattern: Optional[str] = None, 
                               target_suffix: str = "_forge", 
                               dry_run: bool = False, 
                               verbose: bool = False, 
                               exclude: Optional[str] = None, 
                               max_parallel: int = 1, 
                               backup: bool = True, 
                               search_paths: Optional[List[str]] = None) -> bool:
    """Convert multiple environments matching a pattern."""
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


# =========== MAIN FUNCTION ===========

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Single environment options
    parser.add_argument("-s", "--source-env", help="Name of the source Anaconda environment")
    parser.add_argument("-t", "--target-env", help="Name for the new conda-forge environment")
    
    # Batch conversion options
    parser.add_argument("--batch", action="store_true", help="Convert multiple environments")
    parser.add_argument("--pattern", help="Pattern for matching environment names (e.g., 'data*')")
    parser.add_argument("--exclude", help="Comma-separated list of environments to exclude")
    parser.add_argument("--target-suffix", default="_forge", 
                      help="Suffix to add to target environment names in batch mode (default: _forge)")
    
    # Environment search paths
    parser.add_argument("--search-path", action="append", 
                      help="Path to search for conda environments (can be specified multiple times)")
    parser.add_argument("--search-depth", type=int, default=3,
                      help="Maximum directory depth when searching for environments (default: 3)")
    
    # Performance and resource options
    parser.add_argument("--max-parallel", type=int, default=1, 
                      help="Maximum number of parallel conversions (default: 1)")
    parser.add_argument("--no-backup", action="store_true", 
                      help="Skip backing up environment specifications")
    
    # Python version
    parser.add_argument("--python", help="Specify Python version for the new environment")
    
    # Output control
    parser.add_argument("--dry-run", action="store_true", 
                      help="Show what would be installed without creating environments")
    parser.add_argument("--verbose", "-v", action="store_true", 
                      help="Show detailed output of conda commands")
    parser.add_argument("--log-file", 
                      help="Path to log file for detailed logging")
    
    args = parser.parse_args()
    
    # Setup logging with global logger
    setup_logging(args.log_file, args.verbose)
    
    if args.batch:
        # Batch mode - convert multiple environments
        success = convert_multiple_environments(
            args.pattern,
            args.target_suffix,
            args.dry_run,
            args.verbose,
            args.exclude,
            args.max_parallel,
            not args.no_backup,
            args.search_path
        )
    else:
        # Single environment mode
        if not args.source_env:
            parser.error("In single environment mode, --source-env is required")
        
        # Check if the source environment exists or is a path
        env_dict = list_all_conda_environments(
            search_paths=args.search_path, 
            verbose=args.verbose
        )
        
        env_path = None
        if args.source_env in env_dict:
            env_path = env_dict[args.source_env]
            if args.verbose:
                logger.debug(f"Found source environment: {args.source_env} at {env_path}")
        elif os.path.isdir(args.source_env) and is_conda_environment(args.source_env):
            # If the source_env is a path and is a conda environment
            env_path = args.source_env
            args.source_env = os.path.basename(args.source_env)
            if args.verbose:
                logger.debug(f"Using environment at path: {env_path}")
        elif args.search_path:
            logger.error(f"Environment '{args.source_env}' not found in registered environments or search paths")
            sys.exit(1)
        
        success = convert_environment(
            args.source_env,
            args.target_env,
            args.python,
            args.dry_run,
            args.verbose,
            env_path
        )
    
    if not success and not args.dry_run:
        sys.exit(1)


if __name__ == "__main__":
    main()
