"""Reporting module for environment conversions."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, TypeAlias

import yaml

from .utils import PathLike, is_command_output_str, run_command

# Create a logger
logger = logging.getLogger("conda_converter")

# Type definitions
ReportData: TypeAlias = dict[str, Any]
ConversionReport: TypeAlias = dict[str, Any]


def generate_conversion_report(
    source_env: str,
    target_env: str,
    success: bool,
    details: dict[str, Any] | None = None,
    output_file: PathLike | None = None,
    verbose: bool = False,
) -> ConversionReport:
    """Generate a report about the conversion from source to target environment.

    Args:
        source_env: Name of the source environment
        target_env: Name of the target environment
        success: Whether the conversion was successful
        details: Additional details about the conversion
        output_file: Path to write the report to (if specified)
        verbose: Whether to log detailed information

    Returns:
        Dictionary with report information

    """
    # Create a report structure
    report: ConversionReport = {
        "source_environment": source_env,
        "target_environment": target_env,
        "conversion_time": datetime.now().isoformat(),
        "success": success,
        "source_info": {},
        "target_info": {},
        "changes": {},
    }

    # Add any additional details if provided
    if details:
        report["details"] = details

    # Get source environment information
    source_info = _collect_environment_info(source_env, verbose)
    if source_info:
        report["source_info"] = source_info

    # If conversion was successful, get target environment information
    if success:
        target_info = _collect_environment_info(target_env, verbose)
        if target_info:
            report["target_info"] = target_info

            # Calculate changes between environments
            report["changes"] = _calculate_changes(source_info, target_info)

    # Write report to file if requested
    if output_file:
        _write_report(report, output_file, verbose)

    return report


def _collect_environment_info(env_name: str, verbose: bool) -> dict[str, Any]:
    """Collect information about a conda environment.

    Args:
        env_name: Name of the environment
        verbose: Whether to log detailed information

    Returns:
        Dictionary with environment information

    """
    env_info: dict[str, Any] = {
        "name": env_name,
        "python_version": None,
        "conda_packages": [],
        "pip_packages": [],
        "total_packages": 0,
        "channels": {},
    }

    # Get environment path
    env_path = _get_environment_path(env_name, verbose)
    if env_path:
        env_info["path"] = env_path

    # Get package information
    cmd = ["conda", "list", "--name", env_name, "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        logger.warning(f"Could not collect information for environment '{env_name}'")
        return env_info

    try:
        packages = json.loads(output)

        # Extract package information
        conda_packages = []
        pip_packages = []
        channels = {}

        for pkg in packages:
            pkg_info = {
                "name": pkg.get("name", "unknown"),
                "version": pkg.get("version", "unknown"),
                "build": pkg.get("build", ""),
            }

            channel = pkg.get("channel", "unknown")

            # Count packages by channel
            if channel in channels:
                channels[channel] += 1
            else:
                channels[channel] = 1

            # Separate conda and pip packages
            if channel == "pypi":
                pip_packages.append(pkg_info)
            else:
                conda_packages.append(pkg_info)

            # Find Python version
            if pkg.get("name") == "python":
                env_info["python_version"] = pkg.get("version")

        # Add information to the report
        env_info["conda_packages"] = conda_packages
        env_info["pip_packages"] = pip_packages
        env_info["total_packages"] = len(conda_packages) + len(pip_packages)
        env_info["channels"] = channels

        return env_info
    except Exception as e:
        logger.warning(f"Error collecting environment information: {str(e)}")
        return env_info


def _get_environment_path(env_name: str, verbose: bool) -> str | None:
    """Get the path to a conda environment.

    Args:
        env_name: Name of the environment
        verbose: Whether to log detailed information

    Returns:
        Path to the environment or None if not found

    """
    cmd = ["conda", "env", "list", "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        return None

    try:
        env_list = json.loads(output)
        envs = env_list.get("envs", [])

        # Find the environment
        for path in envs:
            if os.path.basename(path) == env_name or path.endswith(f"envs/{env_name}"):
                return path
    except Exception:
        pass

    return None


def _calculate_changes(source_info: dict[str, Any], target_info: dict[str, Any]) -> dict[str, Any]:
    """Calculate changes between source and target environments.

    Args:
        source_info: Information about the source environment
        target_info: Information about the target environment

    Returns:
        Dictionary with changes information

    """
    changes: dict[str, Any] = {
        "package_counts": {
            "source": {
                "conda": len(source_info.get("conda_packages", [])),
                "pip": len(source_info.get("pip_packages", [])),
                "total": source_info.get("total_packages", 0),
            },
            "target": {
                "conda": len(target_info.get("conda_packages", [])),
                "pip": len(target_info.get("pip_packages", [])),
                "total": target_info.get("total_packages", 0),
            },
        },
        "python_version": {
            "source": source_info.get("python_version"),
            "target": target_info.get("python_version"),
            "changed": source_info.get("python_version") != target_info.get("python_version"),
        },
        "changed_packages": [],
        "added_packages": [],
        "removed_packages": [],
        "channel_changes": {},
    }

    # Find changed, added, and removed packages
    source_conda_pkgs = {pkg["name"]: pkg for pkg in source_info.get("conda_packages", [])}
    target_conda_pkgs = {pkg["name"]: pkg for pkg in target_info.get("conda_packages", [])}

    # Find changes in conda packages
    for name, source_pkg in source_conda_pkgs.items():
        if name in target_conda_pkgs:
            target_pkg = target_conda_pkgs[name]

            if (
                source_pkg["version"] != target_pkg["version"]
                or source_pkg["build"] != target_pkg["build"]
            ):
                changes["changed_packages"].append(
                    {
                        "name": name,
                        "source_version": source_pkg["version"],
                        "target_version": target_pkg["version"],
                        "source_build": source_pkg["build"],
                        "target_build": target_pkg["build"],
                    }
                )
        else:
            changes["removed_packages"].append(
                {
                    "name": name,
                    "version": source_pkg["version"],
                    "build": source_pkg["build"],
                }
            )

    # Find added packages
    for name, target_pkg in target_conda_pkgs.items():
        if name not in source_conda_pkgs:
            changes["added_packages"].append(
                {
                    "name": name,
                    "version": target_pkg["version"],
                    "build": target_pkg["build"],
                }
            )

    # Calculate channel changes
    source_channels = source_info.get("channels", {})
    target_channels = target_info.get("channels", {})

    all_channels = set(source_channels.keys()) | set(target_channels.keys())
    for channel in all_channels:
        source_count = source_channels.get(channel, 0)
        target_count = target_channels.get(channel, 0)

        changes["channel_changes"][channel] = {
            "source": source_count,
            "target": target_count,
            "difference": target_count - source_count,
        }

    return changes


def _write_report(report: ConversionReport, output_file: PathLike, verbose: bool) -> None:
    """Write a report to file.

    Args:
        report: Report data
        output_file: Path to write the report to
        verbose: Whether to log detailed information

    """
    output_path = Path(output_file)

    # Create parent directories if needed
    os.makedirs(output_path.parent, exist_ok=True)

    # Determine format based on extension
    ext = output_path.suffix.lower()

    try:
        if ext == ".json":
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
        elif ext in (".yml", ".yaml"):
            with open(output_path, "w") as f:
                yaml.dump(report, f, sort_keys=False)
        else:
            # Default to JSON if format is not recognized
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)

        logger.info(f"Report written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write report: {str(e)}")


def generate_summary_report(
    conversion_results: dict[str, list], output_file: PathLike | None = None
) -> dict[str, Any]:
    """Generate a summary report for multiple conversions.

    Args:
        conversion_results: Results of multiple conversions
        output_file: Path to write the report to (if specified)

    Returns:
        Dictionary with summary information

    """
    # Create a summary structure
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_environments": sum(len(envs) for envs in conversion_results.values()),
        "successful": len(conversion_results.get("success", [])),
        "failed": len(conversion_results.get("failed", [])),
        "skipped": len(conversion_results.get("skipped", [])),
        "success_rate": 0.0,
        "details": conversion_results,
    }

    # Calculate success rate
    total_attempted = summary["successful"] + summary["failed"]
    if total_attempted > 0:
        summary["success_rate"] = round(summary["successful"] / total_attempted * 100, 1)

    # Write report to file if requested
    if output_file:
        _write_report(summary, output_file, False)

    return summary


def print_report_summary(report: ConversionReport) -> None:
    """Print a human-readable summary of a conversion report.

    Args:
        report: Report data to print

    """
    print("\n=== Environment Conversion Report ===")
    print(f"Source: {report['source_environment']}")
    print(f"Target: {report['target_environment']}")
    print(f"Status: {'SUCCESS' if report['success'] else 'FAILED'}")

    if not report["success"]:
        print("\nConversion failed - no further details available")
        return

    # Python version
    changes = report.get("changes", {})
    py_changes = changes.get("python_version", {})

    if py_changes.get("changed"):
        print(f"\nPython version changed: {py_changes.get('source')} -> {py_changes.get('target')}")
    else:
        print(f"\nPython version unchanged: {py_changes.get('source')}")

    # Package counts
    pkg_counts = changes.get("package_counts", {})
    source_counts = pkg_counts.get("source", {})
    target_counts = pkg_counts.get("target", {})

    print("\nPackage Counts:")
    print(
        f"  Source: {source_counts.get('total')} total ({source_counts.get('conda')} conda, {source_counts.get('pip')} pip)"
    )
    print(
        f"  Target: {target_counts.get('total')} total ({target_counts.get('conda')} conda, {target_counts.get('pip')} pip)"
    )

    # Package changes
    changed = changes.get("changed_packages", [])
    added = changes.get("added_packages", [])
    removed = changes.get("removed_packages", [])

    print("\nPackage Changes:")
    print(f"  Changed: {len(changed)} packages")
    print(f"  Added: {len(added)} packages")
    print(f"  Removed: {len(removed)} packages")

    # Channel changes
    channel_changes = changes.get("channel_changes", {})
    print("\nChannel Distribution:")
    for channel, counts in channel_changes.items():
        if channel != "pypi":  # Skip pip packages, they're counted separately
            print(f"  {channel}: {counts.get('source', 0)} -> {counts.get('target', 0)}")

    # Conda-forge percentage
    target_conda_count = target_counts.get("conda", 0)
    conda_forge_count = channel_changes.get("conda-forge", {}).get("target", 0)

    if target_conda_count > 0:
        conda_forge_percent = round(conda_forge_count / target_conda_count * 100, 1)
        print(
            f"\nConda-forge packages: {conda_forge_count} ({conda_forge_percent}% of conda packages)"
        )

    print("\nDetails about these changes are available in the full report.")
    print("======================================")
