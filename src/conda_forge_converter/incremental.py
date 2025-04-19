"""Incremental update functionality for conda-forge environments.

This module provides functionality for updating existing conda-forge environments
and detecting drift between environments. It allows for incremental updates to
environments rather than full conversions, which can be more efficient for
maintaining environments over time.

The module is organized into the following functional areas:

Environment Analysis:
  - get_environment_packages: Get packages from a conda environment
  - find_source_environment: Find the source environment for a conda-forge environment
  - compare_environments: Compare packages between two environments

Drift Detection:
  - detect_drift: Detect drift between a conda-forge environment and its source
  - calculate_environment_similarity: Calculate similarity percentage between environments

Environment Updates:
  - update_conda_forge_environment: Update an existing conda-forge environment
  - update_packages: Update specific packages in an environment
  - add_missing_packages: Add packages that exist in source but not in target

The update process typically includes:
1. Environment Analysis: Analyzing the target environment and its source
2. Package Selection: Determining which packages to update based on options
3. Package Updates: Updating selected packages to their latest versions
4. Missing Package Addition: Adding packages that exist in source but not in target
5. Verification: Verifying that the environment still functions correctly

Type Definitions:
  - PackageSet: Dictionary mapping package names to versions
  - UpdateResult: Dictionary containing update results
"""

import json
import logging
from datetime import datetime
from typing import Any, TypeAlias

from .core import environment_exists
from .utils import is_command_output_str, run_command

# Create a logger
logger = logging.getLogger("conda_converter")

# Type definitions
PackageSet: TypeAlias = dict[str, str]  # name -> version
UpdateResult: TypeAlias = dict[str, Any]


def get_environment_packages(env_name: str, verbose: bool = False) -> PackageSet:
    """Get packages from a conda environment.

    Args:
        env_name: Name of the environment
        verbose: Whether to log detailed information

    Returns:
        Dictionary mapping package names to versions

    """
    packages: PackageSet = {}

    cmd = ["conda", "list", "--name", env_name, "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        logger.error(f"Could not list packages in environment '{env_name}'")
        return packages

    try:
        pkg_list = json.loads(output)
        for pkg in pkg_list:
            name = pkg.get("name")
            version = pkg.get("version")

            if name and version and pkg.get("channel") != "pypi":  # Exclude pip packages
                packages[name] = version
    except Exception as e:
        logger.error(f"Error parsing package list: {e!s}")

    return packages


def check_for_updates(env_name: str, verbose: bool = False) -> tuple[list[dict], list[dict]]:
    """Check for package updates from source to target environment.

    Args:
        env_name: Name of the conda-forge environment to check
        verbose: Whether to log detailed information

    Returns:
        Tuple of (outdated_packages, source_only_packages)

    """
    # Assume convention that source env is env_name without _forge suffix
    source_env = (
        env_name.replace("_forge", "") if env_name.endswith("_forge") else f"{env_name}_source"
    )

    logger.info(f"Checking for updates from '{source_env}' to '{env_name}'")

    # Make sure both environments exist
    if not environment_exists(source_env, verbose):
        logger.error(f"Source environment '{source_env}' does not exist")
        return [], []

    if not environment_exists(env_name, verbose):
        logger.error(f"Target environment '{env_name}' does not exist")
        return [], []

    # Get packages from both environments
    source_packages = get_environment_packages(source_env, verbose)
    target_packages = get_environment_packages(env_name, verbose)

    logger.info(f"Found {len(source_packages)} packages in '{source_env}'")
    logger.info(f"Found {len(target_packages)} packages in '{env_name}'")

    # Find outdated packages (packages in both envs with different versions)
    outdated_packages = []
    for name, source_version in source_packages.items():
        if name in target_packages:
            target_version = target_packages[name]

            if source_version != target_version:
                outdated_packages.append(
                    {
                        "name": name,
                        "source_version": source_version,
                        "target_version": target_version,
                    }
                )

    # Find packages only in source env
    source_only = []
    for name, version in source_packages.items():
        if name not in target_packages:
            source_only.append(
                {
                    "name": name,
                    "version": version,
                }
            )

    # Log summary
    logger.info(f"Found {len(outdated_packages)} outdated packages")
    logger.info(f"Found {len(source_only)} packages only in source environment")

    return outdated_packages, source_only


def update_conda_forge_environment(  # noqa: C901
    env_name: str,
    update_all: bool = False,
    add_missing: bool = False,
    specific_packages: list[str] | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> UpdateResult:
    """Update a conda-forge environment based on its source environment.

    Args:
        env_name: Name of the conda-forge environment to update
        update_all: Whether to update all outdated packages
        add_missing: Whether to add packages missing in target but present in source
        specific_packages: List of specific packages to update
        dry_run: Whether to simulate the operation
        verbose: Whether to log detailed information

    Returns:
        Dictionary with update results

    """
    # Assume convention that source env is env_name without _forge suffix
    source_env = (
        env_name.replace("_forge", "") if env_name.endswith("_forge") else f"{env_name}_source"
    )

    # Prepare result structure
    result: UpdateResult = {
        "source_environment": source_env,
        "target_environment": env_name,
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "outdated_packages": [],
        "updated_packages": [],
        "failed_updates": [],
        "added_packages": [],
        "failed_additions": [],
    }

    # Check for updates
    outdated_packages, source_only_packages = check_for_updates(env_name, verbose)
    result["outdated_packages"] = outdated_packages

    # Return early if nothing to do
    if not outdated_packages and not source_only_packages:
        logger.info(f"Environment '{env_name}' is up to date with '{source_env}'")
        return result

    # Determine which packages to update
    packages_to_update = []

    if specific_packages:
        # Update specific packages
        specific_set = set(specific_packages)
        packages_to_update = [pkg for pkg in outdated_packages if pkg["name"] in specific_set]
    elif update_all:
        # Update all outdated packages
        packages_to_update = outdated_packages
    else:
        # By default, don't update any packages (just report outdated ones)
        pass

    # Update packages if there are any
    if packages_to_update:
        if dry_run:
            logger.info(f"Would update {len(packages_to_update)} packages in '{env_name}'")
            result["updated_packages"] = [p["name"] for p in packages_to_update]
        else:
            # Update packages one by one to handle failures
            for pkg in packages_to_update:
                pkg_name = pkg["name"]
                pkg_version = pkg["source_version"]

                logger.info(f"Updating {pkg_name}={pkg_version} in '{env_name}'")
                success = _update_package(env_name, pkg_name, pkg_version, verbose)

                if success:
                    logger.info(f"Successfully updated {pkg_name}")
                    result["updated_packages"].append(pkg_name)
                else:
                    logger.error(f"Failed to update {pkg_name}")
                    result["failed_updates"].append(pkg_name)

    # Add missing packages if requested
    if add_missing and source_only_packages:
        if dry_run:
            logger.info(f"Would add {len(source_only_packages)} missing packages to '{env_name}'")
            result["added_packages"] = [p["name"] for p in source_only_packages]
        else:
            # Add packages one by one
            for pkg in source_only_packages:
                pkg_name = pkg["name"]
                pkg_version = pkg["version"]

                logger.info(f"Adding {pkg_name}={pkg_version} to '{env_name}'")
                success = _update_package(env_name, pkg_name, pkg_version, verbose)

                if success:
                    logger.info(f"Successfully added {pkg_name}")
                    result["added_packages"].append(pkg_name)
                else:
                    logger.error(f"Failed to add {pkg_name}")
                    result["failed_additions"].append(pkg_name)

    # Log summary
    if not dry_run:
        updated_count = len(result["updated_packages"])
        added_count = len(result["added_packages"])
        failed_count = len(result["failed_updates"]) + len(result["failed_additions"])

        if updated_count > 0 or added_count > 0:
            logger.info(
                f"Updated {updated_count} packages and added {added_count} packages in '{env_name}'"
            )

        if failed_count > 0:
            logger.warning(f"{failed_count} packages failed to update/add")

    return result


def _update_package(env_name: str, package_name: str, package_version: str, verbose: bool) -> bool:
    """Update a single package in a conda environment.

    Args:
        env_name: Name of the environment
        package_name: Name of the package to update
        package_version: Version of the package to update to
        verbose: Whether to log detailed information

    Returns:
        True if the update succeeded, False otherwise

    """
    cmd = [
        "conda",
        "install",
        "--name",
        env_name,
        "--channel",
        "conda-forge",
        "--override-channels",
        "--yes",
        f"{package_name}={package_version}",
    ]

    if verbose:
        logger.info(f"Running: {' '.join(cmd)}")

    result = run_command(cmd, verbose)
    return result is not None and result is not False


def compare_environments(source_env: str, target_env: str, verbose: bool = False) -> dict[str, Any]:
    """Compare two environments to identify differences.

    Args:
        source_env: Name of the source environment
        target_env: Name of the target environment
        verbose: Whether to log detailed information

    Returns:
        Dictionary with comparison results

    """
    # Make sure both environments exist
    if not environment_exists(source_env, verbose):
        logger.error(f"Source environment '{source_env}' does not exist")
        return {"error": f"Source environment '{source_env}' does not exist"}

    if not environment_exists(target_env, verbose):
        logger.error(f"Target environment '{target_env}' does not exist")
        return {"error": f"Target environment '{target_env}' does not exist"}

    # Get packages from both environments
    source_packages = get_environment_packages(source_env, verbose)
    target_packages = get_environment_packages(target_env, verbose)

    # Compare packages
    source_only = []
    target_only = []
    different_versions = []
    same_versions = []

    # Find packages in source but not in target
    for name, version in source_packages.items():
        if name not in target_packages:
            source_only.append({"name": name, "version": version})
        else:
            target_version = target_packages[name]
            if version == target_version:
                same_versions.append({"name": name, "version": version})
            else:
                different_versions.append(
                    {
                        "name": name,
                        "source_version": version,
                        "target_version": target_version,
                    }
                )

    # Find packages in target but not in source
    for name, version in target_packages.items():
        if name not in source_packages:
            target_only.append({"name": name, "version": version})

    # Compile results
    result = {
        "source_environment": source_env,
        "target_environment": target_env,
        "source_package_count": len(source_packages),
        "target_package_count": len(target_packages),
        "source_only": source_only,
        "target_only": target_only,
        "different_versions": different_versions,
        "same_versions": same_versions,
    }

    # Calculate drift metrics
    total_packages = len(source_packages) | len(target_packages)
    if total_packages > 0:
        env_similarity = round(len(same_versions) / total_packages * 100, 1)
        result["environment_similarity"] = env_similarity

        if len(source_packages) > 0:
            source_coverage = round(
                (len(same_versions) + len(different_versions)) / len(source_packages) * 100, 1
            )
            result["source_coverage"] = source_coverage

    # Log summary
    logger.info(f"Environments have {len(same_versions)} packages with same version")
    logger.info(f"Found {len(different_versions)} packages with different versions")
    logger.info(f"Found {len(source_only)} packages only in '{source_env}'")
    logger.info(f"Found {len(target_only)} packages only in '{target_env}'")

    return result


def detect_drift(env_name: str, verbose: bool = False) -> dict[str, Any]:
    """Detect drift between a conda-forge environment and its source.

    Args:
        env_name: Name of the conda-forge environment to check
        verbose: Whether to log detailed information

    Returns:
        Dictionary with drift metrics

    """
    # Determine the source environment name
    source_env = (
        env_name.replace("_forge", "") if env_name.endswith("_forge") else f"{env_name}_source"
    )

    # Compare the environments
    return compare_environments(source_env, env_name, verbose)
