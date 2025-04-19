"""Reporting module for environment conversions.

This module provides functionality for generating detailed reports about environment
conversions, including information about packages, conversion success, and other metrics.
These reports can be used to analyze the conversion process and identify any issues.

The module is organized into the following functional areas:

Report Generation:
  - generate_conversion_report: Generate a detailed report about an environment conversion
  - generate_summary_report: Generate a summary report for batch conversions
  - print_report_summary: Print a summary of a conversion report to the console

Report Data Structures:
  - ReportData: Data structure for report serialization
  - ConversionReport: Class representing a conversion report
  - SummaryReport: Class representing a summary report

Report Structure:
  - Conversion Report: Includes metadata, package information, performance metrics, and issues
  - Summary Report: Includes overall statistics, common issues, and performance metrics

The reports can be saved in different formats (JSON, YAML) and can be used for:
  - Analyzing conversion success and failure rates
  - Identifying common issues across multiple conversions
  - Tracking performance metrics for conversions
  - Documenting the conversion process for audit purposes
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, TypedDict, cast, runtime_checkable

import yaml

from .utils import PathLike, is_command_output_str, run_command

# Create a logger
logger = logging.getLogger("conda_converter")


class ReportData(TypedDict):
    """Data structure for report serialization."""

    source_env: str
    target_env: str
    start_time: str
    end_time: str | None
    success: bool
    errors: list[str]
    warnings: list[str]
    packages: dict[str, list[dict[str, str]]]
    metadata: dict[str, Any]


@runtime_checkable
class ReportProtocol(Protocol):
    """Protocol defining the interface for report objects."""

    def to_dict(self) -> ReportData:
        """Convert the report to a dictionary format."""
        ...

    def __getitem__(self, key: str) -> str | bool | list | dict:
        """Get a value from the report by key."""
        ...

    def get(
        self, key: str, default: str | bool | list | dict | None = None
    ) -> str | bool | list | dict | None:
        """Get a value from the report by key with a default fallback."""
        ...


@dataclass
class ConversionReport:
    """Report for environment conversion operations."""

    source_env: str
    target_env: str
    start_time: datetime
    end_time: datetime | None
    success: bool
    errors: list[str]
    warnings: list[str]
    packages: dict[str, list[dict[str, str]]]
    metadata: dict[str, Any]

    @classmethod
    def create(cls, source_env: str, target_env: str) -> "ConversionReport":
        """Create a new conversion report."""
        return cls(
            source_env=source_env,
            target_env=target_env,
            start_time=datetime.now(),
            end_time=None,
            success=False,
            errors=[],
            warnings=[],
            packages={"conda": [], "pip": []},
            metadata={},
        )

    def add_error(self, error: str) -> None:
        """Add an error to the report."""
        self.errors.append(error)
        logger.error(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning to the report."""
        self.warnings.append(warning)
        logger.warning(warning)

    def add_package(self, name: str, version: str, source: str = "conda") -> None:
        """Add a package to the report."""
        if source not in self.packages:
            self.packages[source] = []
        self.packages[source].append({"name": name, "version": version})

    def add_metadata(self, key: str, value: str | float | bool | list | dict) -> None:
        """Add metadata to the report."""
        self.metadata[key] = value

    def complete(self, success: bool = True) -> None:
        """Mark the report as complete."""
        self.end_time = datetime.now()
        self.success = success

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat() if self.end_time else None
        return data


def generate_conversion_report(
    source_env: str,
    target_env: str,
    success: bool,
    details: dict[str, Any] | None = None,
    output_file: PathLike | None = None,
    verbose: bool = False,
) -> ConversionReport:
    """Generate a detailed report of the environment conversion.

    Args:
        source_env: Name of the source environment
        target_env: Name of the target environment
        success: Whether the conversion was successful
        details: Additional details about the conversion
        output_file: Optional path to save the report
        verbose: Whether to log detailed information

    Returns:
        Conversion report containing details about the conversion

    """
    # Create a report structure
    report = ConversionReport.create(source_env, target_env)

    # Add any additional details if provided
    if details:
        report.metadata["details"] = details

    # Get source environment information
    source_info = _collect_environment_info(source_env, verbose)
    if source_info:
        report.metadata["source_info"] = source_info

    # If conversion was successful, get target environment information
    if success:
        target_info = _collect_environment_info(target_env, verbose)
        if target_info:
            report.metadata["target_info"] = target_info

            # Calculate changes between environments
            report.metadata["changes"] = _calculate_changes(source_info, target_info)

    # Set success status
    report.success = success
    report.complete(success)

    # Write report to file if requested
    if output_file:
        _write_report(report, output_file)

    return report


def _collect_environment_info(env_name: str, verbose: bool) -> dict[str, Any]:
    """Collect information about an environment.

    Args:
        env_name: Name of the environment
        verbose: Whether to log detailed information

    Returns:
        Dictionary containing environment information

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
    env_path = _find_environment_path(env_name)
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
        logger.warning(f"Error collecting environment information: {e!s}")
        return env_info


def _find_environment_path(env_name: str) -> str | None:
    """Find the path of an environment.

    Args:
        env_name: Name of the environment

    Returns:
        Path to the environment, or None if not found

    """
    try:
        result = run_command(["conda", "env", "list", "--json"], verbose=True)
        if not isinstance(result, str):
            return None

        envs_data = json.loads(result)
        envs = envs_data.get("envs", [])

        for path in envs:
            try:
                if Path(path).name == env_name or path.endswith(f"envs/{env_name}"):
                    return path
            except Exception as e:
                logger.debug(f"Error checking path {path}: {e!s}")
                continue

        return None
    except Exception as e:
        logger.error(f"Error finding environment path: {e!s}")
        return None


def _calculate_changes(source_info: dict[str, Any], target_info: dict[str, Any]) -> dict[str, Any]:
    """Calculate changes between source and target environments.

    Args:
        source_info: Information about the source environment
        target_info: Information about the target environment

    Returns:
        Dictionary containing the changes

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


def _write_report(report: ConversionReport, output_file: PathLike) -> None:
    """Write a report to file.

    Args:
        report: Report to write
        output_file: Path to write the report to

    """
    output_path = Path(output_file)

    # Create parent directories if needed
    os.makedirs(output_path.parent, exist_ok=True)

    # Determine format based on extension
    ext = output_path.suffix.lower()

    try:
        if ext == ".json":
            with Path(output_path).open("w") as f:
                json.dump(report.to_dict(), f, indent=2)
        elif ext in (".yml", ".yaml"):
            with Path(output_path).open("w") as f:
                yaml.dump(report.to_dict(), f, sort_keys=False)
        else:
            # Default to JSON if format is not recognized
            with Path(output_path).open("w") as f:
                json.dump(report.to_dict(), f, indent=2)

        logger.info(f"Report written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write report: {e!s}")


def generate_summary_report(
    conversion_results: dict[str, list], output_file: PathLike | None = None
) -> dict[str, Any]:
    """Generate a summary report of the conversion results.

    Args:
        conversion_results: Results of multiple conversions
        output_file: Optional path to save the report

    Returns:
        Summary report containing key metrics and statistics

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
        # Create a temporary ConversionReport to use the _write_report function
        temp_report = ConversionReport.create("summary", "summary")
        temp_report.metadata = summary
        _write_report(temp_report, output_file)

    return summary


def print_report_summary(report: ConversionReport) -> None:
    """Print a summary of the conversion report.

    Args:
        report: Report to summarize

    """
    print("\n=== Environment Conversion Report ===")
    print(f"Source: {report.source_env}")
    print(f"Target: {report.target_env}")
    print(f"Status: {'SUCCESS' if report.success else 'FAILED'}")

    if not report.success:
        print("\nConversion failed - no further details available")
        return

    # Python version
    changes = report.metadata.get("changes", {})
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
        f"  Source: {source_counts.get('total')} total ({source_counts.get('conda')} conda, {source_counts.get('pip')} pip)"  # noqa: E501
    )
    print(
        f"  Target: {target_counts.get('total')} total ({target_counts.get('conda')} conda, {target_counts.get('pip')} pip)"  # noqa: E501
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
            f"\nConda-forge packages: {conda_forge_count} "
            f"({conda_forge_percent}% of conda packages)"
        )

    print("\nDetails about these changes are available in the full report.")
    print("======================================")


class ReportError(Exception):
    """Exception raised for errors in report handling."""

    INVALID_FORMAT = "Invalid report format: expected dictionary"
    MISSING_FIELD = "Missing required field: {field}"
    INVALID_TYPE = "Invalid type for field {field}: expected {expected}"
    READ_ERROR = "Failed to read report"


def _validate_report_data(data: dict) -> None:
    """Validate report data structure.

    Args:
        data: Data to validate

    Raises:
        ReportError: If the data is invalid

    """
    if not isinstance(data, dict):
        raise ReportError(ReportError.INVALID_FORMAT)

    required_fields = {
        "source_env": str,
        "target_env": str,
        "start_time": str,
        "success": bool,
        "errors": list,
        "warnings": list,
        "packages": dict,
        "metadata": dict,
    }

    for field, field_type in required_fields.items():
        if field not in data:
            raise ReportError(ReportError.MISSING_FIELD.format(field=field))
        if not isinstance(data[field], field_type):
            raise ReportError(
                ReportError.INVALID_TYPE.format(field=field, expected=field_type.__name__)
            )


def read_report(report_file: PathLike) -> ConversionReport:
    """Read a report from file.

    Args:
        report_file: Path to the report file

    Returns:
        ConversionReport object

    Raises:
        ReportError: If the report file cannot be read or is invalid

    """
    try:
        with Path(report_file).open("r", encoding="utf-8") as f:
            data = json.load(f)
            _validate_report_data(data)

            return ConversionReport(
                source_env=str(data["source_env"]),
                target_env=str(data["target_env"]),
                start_time=datetime.fromisoformat(str(data["start_time"])),
                end_time=datetime.fromisoformat(str(data["end_time"]))
                if data.get("end_time")
                else None,
                success=bool(data["success"]),
                errors=list(map(str, data["errors"])),
                warnings=list(map(str, data["warnings"])),
                packages=cast(dict[str, list[dict[str, str]]], data["packages"]),
                metadata=cast(dict[str, Any], data["metadata"]),
            )
    except Exception as e:
        logger.error(f"Failed to read report from {report_file}: {e}")
        raise ReportError(ReportError.READ_ERROR) from e
