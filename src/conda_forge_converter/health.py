"""Health check functionality for conda environments.

This module provides functionality for analyzing and verifying conda environments
for potential issues. It helps identify problems with environments before and after
conversion, ensuring that environments are functioning correctly.

The module is organized into the following functional areas:

Health Analysis:
  - check_environment_health: Analyze an environment for potential issues
  - check_package_conflicts: Check for known package conflicts
  - check_environment_structure: Verify the environment's directory structure

Environment Verification:
  - verify_environment: Verify that an environment functions correctly
  - run_basic_tests: Run basic tests to ensure the environment works
  - run_package_tests: Test key packages to ensure they function correctly

The health check process typically includes:
1. Package Inventory: Listing all installed packages and their versions
2. Dependency Analysis: Checking for missing or conflicting dependencies
3. Environment Structure: Verifying the environment's directory structure
4. Python Functionality: Testing basic Python functionality
5. Package Imports: Attempting to import key packages

Type Definitions:
  - HealthStatus: Status of a health check ("GOOD", "WARNING", "ERROR")
  - HealthCheckResult: Dictionary containing health check results

Constants:
  - CONFLICT_PACKAGES: Dictionary of packages with known conflict versions
"""

import json
import logging
import os
import shutil
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any, Literal, TypeAlias

from .utils import is_command_output_str, run_command

# Create a logger
logger = logging.getLogger("conda_converter")

# Type definitions
HealthStatus: TypeAlias = Literal["GOOD", "WARNING", "ERROR"]
HealthCheckResult: TypeAlias = dict[str, Any]

# Common package conflicts
CONFLICT_PACKAGES: dict[str, str] = {
    "numpy": "1.24.0",
    "pandas": "2.0.0",
    "scipy": "1.10.0",
    "matplotlib": "3.7.0",
    "scikit-learn": "1.2.0",
}


def check_environment_health(env_name: str, verbose: bool = False) -> HealthCheckResult:
    """Check the health of a conda environment.

    Args:
        env_name: Name of the environment to check
        verbose: Whether to log detailed information

    Returns:
        Dictionary with health check results

    """
    result: HealthCheckResult = {
        "name": env_name,
        "status": "GOOD",
        "issues": [],
        "details": {},
    }

    # Run a series of health checks
    _check_environment_exists(env_name, result, verbose)

    if result["status"] != "ERROR":
        _check_python_version(env_name, result, verbose)
        _check_environment_packages(env_name, result, verbose)
        _check_environment_conflicts(env_name, result, verbose)
        _check_environment_size(env_name, result, verbose)

    # Log results
    issue_count = len(result["issues"])
    if issue_count > 0:
        if result["status"] == "ERROR":
            logger.error(f"Found {issue_count} issues with environment '{env_name}'")
        else:
            logger.warning(f"Found {issue_count} potential issues with environment '{env_name}'")

        for issue in result["issues"]:
            log_func = logger.error if issue.get("severity") == "ERROR" else logger.warning
            log_func(f"- {issue['message']}")
    else:
        logger.info(f"Environment '{env_name}' looks healthy")

    return result


def _check_environment_exists(env_name: str, result: HealthCheckResult, verbose: bool) -> None:
    """Check if the environment exists."""
    cmd = ["conda", "env", "list", "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        result["status"] = "ERROR"
        result["issues"].append(
            {
                "severity": "ERROR",
                "message": "Failed to list conda environments",
                "check": "environment_exists",
            }
        )
        return

    try:
        env_list = json.loads(output)
        env_names = [Path(env).name for env in env_list.get("envs", [])]

        if env_name not in env_names:
            result["status"] = "ERROR"
            result["issues"].append(
                {
                    "severity": "ERROR",
                    "message": f"Environment '{env_name}' does not exist",
                    "check": "environment_exists",
                }
            )
    except json.JSONDecodeError:
        result["status"] = "ERROR"
        result["issues"].append(
            {
                "severity": "ERROR",
                "message": "Could not parse conda environment list output",
                "check": "environment_exists",
            }
        )


def _check_python_version(env_name: str, result: HealthCheckResult, verbose: bool) -> None:
    """Check the Python version in the environment."""
    cmd = ["conda", "list", "--name", env_name, "python", "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        result["status"] = "WARNING"
        result["issues"].append(
            {
                "severity": "WARNING",
                "message": "Could not determine Python version",
                "check": "python_version",
            }
        )
        return

    try:
        package_info = json.loads(output)
        python_info = next((pkg for pkg in package_info if pkg["name"] == "python"), None)

        if not python_info:
            result["status"] = "WARNING"
            result["issues"].append(
                {
                    "severity": "WARNING",
                    "message": "Python not found in environment",
                    "check": "python_version",
                }
            )
            return

        # Store details about the Python version
        result["details"]["python_version"] = python_info.get("version")

        # Check if Python version is nearing end-of-life
        python_version = python_info.get("version", "")
        major_minor = ".".join(python_version.split(".")[:2]) if python_version else ""

        eol_versions = ["3.7", "3.8", "3.9"]  # Example EOL versions
        if major_minor in eol_versions:
            result["status"] = "WARNING"
            result["issues"].append(
                {
                    "severity": "WARNING",
                    "message": f"Python {major_minor} is nearing end-of-life",
                    "check": "python_version",
                }
            )
    except (json.JSONDecodeError, Exception) as e:
        result["status"] = "WARNING"
        result["issues"].append(
            {
                "severity": "WARNING",
                "message": f"Error checking Python version: {e!s}",
                "check": "python_version",
            }
        )


def _check_environment_packages(env_name: str, result: HealthCheckResult, verbose: bool) -> None:
    """Check the packages in the environment."""
    cmd = ["conda", "list", "--name", env_name, "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        result["status"] = "WARNING"
        result["issues"].append(
            {
                "severity": "WARNING",
                "message": "Could not list packages in environment",
                "check": "packages",
            }
        )
        return

    try:
        packages = json.loads(output)

        # Store package counts
        conda_count = sum(1 for pkg in packages if pkg.get("channel") != "pypi")
        pip_count = sum(1 for pkg in packages if pkg.get("channel") == "pypi")

        result["details"]["package_counts"] = {
            "conda": conda_count,
            "pip": pip_count,
            "total": conda_count + pip_count,
        }

        # Check for extremely large number of packages
        if conda_count + pip_count > 200:  # Arbitrary threshold
            result["status"] = "WARNING"
            result["issues"].append(
                {
                    "severity": "WARNING",
                    "message": (
                        f"Environment has a very large number of packages "
                        f"({conda_count + pip_count})"
                    ),
                    "check": "packages",
                }
            )
    except (json.JSONDecodeError, Exception) as e:
        result["status"] = "WARNING"
        result["issues"].append(
            {
                "severity": "WARNING",
                "message": f"Error analyzing packages: {e!s}",
                "check": "packages",
            }
        )


def _check_environment_conflicts(env_name: str, result: HealthCheckResult, verbose: bool) -> None:
    """Check for package conflicts in the environment."""
    cmd = ["conda", "list", "--name", env_name, "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        return  # Already reported in packages check

    try:
        # Check if any packages are duplicated or have version conflicts
        packages = json.loads(output)
        package_names = {}

        for pkg in packages:
            name = pkg.get("name")
            if not name:
                continue

            if name in package_names:
                package_names[name].append(pkg)
            else:
                package_names[name] = [pkg]

        # Find packages with multiple versions
        duplicates = {name: pkgs for name, pkgs in package_names.items() if len(pkgs) > 1}

        if duplicates:
            result["status"] = "WARNING"
            result["issues"].append(
                {
                    "severity": "WARNING",
                    "message": f"Found {len(duplicates)} packages with multiple versions",
                    "check": "conflicts",
                }
            )
            result["details"]["duplicate_packages"] = [
                {"name": name, "versions": [p.get("version") for p in pkgs]}
                for name, pkgs in duplicates.items()
            ]
    except (json.JSONDecodeError, Exception):
        # Skip reporting this error as it's a secondary check
        pass


def _check_environment_size(env_name: str, result: HealthCheckResult, verbose: bool) -> None:
    """Check the size of the environment."""
    # Get environment path first
    env_list_cmd = ["conda", "env", "list", "--json"]
    output = run_command(env_list_cmd, verbose)

    if not is_command_output_str(output):
        return

    try:
        env_data = json.loads(output)
        envs = env_data.get("envs", [])

        # Find the path for this environment
        env_path = None
        for path in envs:
            if Path(path).name == env_name or path.endswith(f"envs/{env_name}"):
                env_path = path
                break

        if not env_path:
            return

        # Calculate size using environment path
        env_size = _calculate_directory_size(env_path)
        result["details"]["size_mb"] = round(env_size / (1024 * 1024), 2)

        # Check if environment is very large
        if env_size > 5 * 1024 * 1024 * 1024:  # 5 GB
            result["status"] = "WARNING"
            result["issues"].append(
                {
                    "severity": "WARNING",
                    "message": f"Environment is very large ({result['details']['size_mb']} MB)",
                    "check": "size",
                }
            )
    except (json.JSONDecodeError, Exception):
        pass  # Skip reporting this error as it's a secondary check


def _calculate_directory_size(directory: str) -> int:
    """Calculate the size of a directory in bytes."""
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            fp = Path(dirpath) / f
            with suppress(OSError, FileNotFoundError):
                total_size += Path(fp).stat().st_size
    return total_size


def verify_environment(
    env_name: str, tests: list[str] | None = None, verbose: bool = False
) -> bool:
    """Verify that an environment is functioning correctly.

    Args:
        env_name: Name of the environment to verify
        tests: List of tests to run (defaults to all tests)
        verbose: Whether to log detailed information

    Returns:
        True if all tests pass, False otherwise

    """
    if tests is None:
        tests = ["import", "run_python", "test_pip"]

    all_passed = True

    for test in tests:
        if test == "import":
            passed = _test_imports(env_name, verbose)
        elif test == "run_python":
            passed = _test_run_python(env_name, verbose)
        elif test == "test_pip":
            passed = _test_pip(env_name, verbose)
        else:
            logger.warning(f"Unknown test: {test}")
            passed = True

        if not passed:
            all_passed = False

    return all_passed


def _test_imports(env_name: str, verbose: bool) -> bool:
    """Test importing common packages in the environment.

    Args:
        env_name: Name of the environment to test
        verbose: Whether to log detailed information

    Returns:
        True if all imports succeed, False otherwise
    """
    # Get list of installed packages
    cmd = ["conda", "list", "--name", env_name, "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        return False

    try:
        packages = json.loads(output)
        test_packages = [
            pkg["name"]
            for pkg in packages
            if pkg["name"] in ["numpy", "pandas", "scipy", "matplotlib", "scikit-learn"]
        ]

        if not test_packages:
            return True  # No common packages to test

        # Create a temporary script to test imports
        script_content = "try:\n"
        for package in test_packages:
            script_content += f"    import {package}\n"
        script_content += '    print("SUCCESS: All imports successful")\n'
        script_content += "except ImportError as e:\n"
        script_content += '    print(f"FAILURE: Import error - {e}")\n'

        # Write the script to a temporary file
        script_path = Path("temp_import_test.py")
        script_path.write_text(script_content)

        try:
            # Run the script in the environment
            cmd = ["conda", "run", "--name", env_name, "python", str(script_path)]
            output = run_command(cmd, verbose)

            if not is_command_output_str(output):
                return False

            return "SUCCESS" in output
        finally:
            # Clean up the temporary file
            script_path.unlink()

    except (json.JSONDecodeError, Exception) as e:
        if verbose:
            logger.error(f"Error testing imports: {e!s}")
        return False


def _test_run_python(env_name: str, verbose: bool) -> bool:
    """Test running Python in the environment."""
    test_cmd = ["conda", "run", "--name", env_name, "python", "-c", "print('Hello, World!')"]
    test_result = run_command(test_cmd, verbose, capture=True)

    if is_command_output_str(test_result) and "Hello, World!" in test_result:
        logger.info(f"Python test passed for environment '{env_name}'")
        return True
    logger.error(f"Python test failed for environment '{env_name}'")
    return False


def _test_pip(env_name: str, verbose: bool) -> bool:
    """Test if pip is working in the environment."""
    test_cmd = ["conda", "run", "--name", env_name, "pip", "--version"]
    test_result = run_command(test_cmd, verbose, capture=True)

    if is_command_output_str(test_result) and "pip" in test_result:
        logger.info(f"Pip test passed for environment '{env_name}'")
        return True
    logger.error(f"Pip test failed for environment '{env_name}'")
    return False


def check_duplicate_packages(env_name: str) -> list[dict[str, Any]]:
    """Check for duplicate packages in an environment."""
    try:
        result = run_command(["conda", "list", "-n", env_name, "--json"], verbose=True)
        if not isinstance(result, str):
            return []

        data = json.loads(result)
        packages = data.get("packages", [])

        # Group packages by name
        package_groups: dict[str, list[str]] = {}
        for pkg in packages:
            name = pkg.get("name", "")
            if name:
                if name not in package_groups:
                    package_groups[name] = []
                package_groups[name].append(pkg.get("version", ""))

        # Find duplicates
        duplicates = {
            name: versions for name, versions in package_groups.items() if len(versions) > 1
        }

        return [
            {
                "name": name,
                "versions": versions,
            }
            for name, versions in duplicates.items()
        ]
    except (json.JSONDecodeError, Exception) as e:
        logger.debug(f"Error checking duplicate packages: {e!s}")
        return []


def check_package_conflicts(env_name: str) -> list[dict[str, Any]]:
    """Check for package conflicts in an environment."""
    try:
        result = run_command(["conda", "list", "-n", env_name, "--json"], verbose=True)
        if not isinstance(result, str):
            return []

        data = json.loads(result)
        packages = data.get("packages", [])

        # Check for common conflicts
        conflicts = []
        for pkg in packages:
            name = pkg.get("name", "")
            version = pkg.get("version", "")
            if name in CONFLICT_PACKAGES and version != CONFLICT_PACKAGES[name]:
                conflicts.append(
                    {
                        "name": name,
                        "current_version": version,
                        "recommended_version": CONFLICT_PACKAGES[name],
                    }
                )

        return conflicts
    except (json.JSONDecodeError, Exception) as e:
        logger.debug(f"Error checking package conflicts: {e!s}")
        return []


def check_package_imports(env_name: str) -> list[str]:
    """Check importing packages in an environment."""
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Write test script
            test_script = temp_dir / f"test_imports_{env_name}.py"
            with test_script.open("w") as f:
                f.write("""
import sys
import importlib

def test_import(package_name):
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

# Test common packages
packages = [
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "scikit-learn",
]

failed_imports = []
for package in packages:
    if not test_import(package):
        failed_imports.append(package)

if failed_imports:
    print("Failed to import:", ", ".join(failed_imports))
    sys.exit(1)
""")

            # Run test script
            cmd = ["conda", "run", "-n", env_name, "python", str(test_script)]
            result = run_command(cmd, verbose=True)

            if not isinstance(result, str):
                return ["Failed to run import tests"]

            if "Failed to import:" in result:
                failed = result.split("Failed to import:")[1].strip()
                return [pkg.strip() for pkg in failed.split(",")]

            return []

        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)

    except Exception as e:
        logger.error(f"Error testing imports: {e!s}")
        return ["Failed to run import tests"]
