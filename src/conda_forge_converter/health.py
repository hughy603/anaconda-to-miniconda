"""Health check functionality for conda environments."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Literal, TypeAlias

from .utils import is_command_output_str, run_command

# Create a logger
logger = logging.getLogger("conda_converter")

# Type definitions
HealthStatus: TypeAlias = Literal["GOOD", "WARNING", "ERROR"]
HealthCheckResult: TypeAlias = dict[str, Any]


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
        env_names = [os.path.basename(env) for env in env_list.get("envs", [])]

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
                "message": f"Error checking Python version: {str(e)}",
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
                    "message": f"Environment has a very large number of packages ({conda_count + pip_count})",
                    "check": "packages",
                }
            )
    except (json.JSONDecodeError, Exception) as e:
        result["status"] = "WARNING"
        result["issues"].append(
            {
                "severity": "WARNING",
                "message": f"Error analyzing packages: {str(e)}",
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
            if os.path.basename(path) == env_name or path.endswith(f"envs/{env_name}"):
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
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except (OSError, FileNotFoundError):
                pass
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
    """Test importing key packages in the environment."""
    # Get a list of installed packages
    cmd = ["conda", "list", "--name", env_name, "--json"]
    output = run_command(cmd, verbose)

    if not is_command_output_str(output):
        logger.error("Could not list packages in environment")
        return False

    try:
        packages = json.loads(output)

        # Select common packages to test importing
        test_packages = ["numpy", "pandas", "matplotlib", "scikit-learn", "tensorflow", "torch"]
        installed_test_packages = [pkg["name"] for pkg in packages if pkg["name"] in test_packages]

        if not installed_test_packages:
            logger.info("No common packages found to test imports")
            return True

        # Create a Python script to test imports
        import_statements = "\n".join([f"import {pkg}" for pkg in installed_test_packages])
        test_script = f"""
try:
    {import_statements}
    print("SUCCESS: All imports successful")
    exit(0)
except Exception as e:
    print(f"FAILURE: Import error - {{str(e)}}")
    exit(1)
"""

        # Write to temporary file
        temp_script = Path(f"/tmp/test_imports_{env_name}.py")
        with open(temp_script, "w") as f:
            f.write(test_script)

        # Run the test script in the environment
        test_cmd = ["conda", "run", "--name", env_name, "python", str(temp_script)]
        test_result = run_command(test_cmd, verbose, capture=True)

        # Clean up
        temp_script.unlink()

        if is_command_output_str(test_result) and "SUCCESS" in test_result:
            logger.info(f"Import test passed for environment '{env_name}'")
            return True
        logger.error(f"Import test failed for environment '{env_name}'")
        return False
    except Exception as e:
        logger.error(f"Error testing imports: {str(e)}")
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
