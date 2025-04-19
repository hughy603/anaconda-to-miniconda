"""Validation framework for post-conversion testing."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .utils import PathLike, is_command_output_str, logger, run_command


@dataclass
class ValidationResult:
    """Results from validation tests."""

    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PackageValidationResult:
    """Results from package validation."""

    name: str
    version: str | None
    installed: bool
    importable: bool
    import_error: str | None = None


class ValidationFramework:
    """Framework for validating converted environments."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the validation framework.

        Args:
            verbose: Whether to log detailed information

        """
        self.verbose = verbose

    def validate_environment(
        self, env_name: str, source_env: str | None = None
    ) -> ValidationResult:
        """Validate a converted environment.

        Args:
            env_name: Name of the environment to validate
            source_env: Name of the source environment (if available)

        Returns:
            Validation result

        """
        if self.verbose:
            logger.info(f"Validating environment '{env_name}'")

        # Check if environment exists
        if not self._environment_exists(env_name):
            return ValidationResult(
                passed=False,
                message=f"Environment '{env_name}' does not exist",
                details={"error": "environment_not_found"},
            )

        # Get environment packages
        packages = self._get_environment_packages(env_name)
        if not packages:
            return ValidationResult(
                passed=False,
                message=f"Failed to get packages for environment '{env_name}'",
                details={"error": "package_list_failed"},
            )

        # Validate packages
        validation_results = self._validate_packages(env_name, packages)

        # Count results
        total = len(validation_results)
        installed = sum(1 for r in validation_results if r.installed)
        importable = sum(1 for r in validation_results if r.installed and r.importable)

        # Determine overall result
        passed = total > 0 and installed == total and importable == total
        message = (
            f"Validation {'passed' if passed else 'failed'}: "
            f"{importable}/{installed}/{total} packages importable/installed/total"
        )

        # Prepare details
        details = {
            "total_packages": total,
            "installed_packages": installed,
            "importable_packages": importable,
            "package_results": [
                {
                    "name": r.name,
                    "version": r.version,
                    "installed": r.installed,
                    "importable": r.importable,
                    "import_error": r.import_error,
                }
                for r in validation_results
            ],
        }

        # Compare with source environment if provided
        if source_env and self._environment_exists(source_env):
            comparison = self._compare_environments(source_env, env_name)
            details["comparison"] = comparison

        return ValidationResult(passed=passed, message=message, details=details)

    def _environment_exists(self, env_name: str) -> bool:
        """Check if an environment exists.

        Args:
            env_name: Name of the environment to check

        Returns:
            True if the environment exists, False otherwise

        """
        try:
            result = run_command(["conda", "env", "list", "--json"], verbose=self.verbose)
            if not is_command_output_str(result):
                return False

            envs_data = json.loads(result)
            envs = envs_data.get("envs", [])
            env_paths = [Path(path).name for path in envs]
            return env_name in env_paths
        except Exception as e:
            logger.error(f"Error checking if environment exists: {e!s}")
            return False

    def _get_environment_packages(self, env_name: str) -> list[dict[str, Any]]:
        """Get packages installed in an environment.

        Args:
            env_name: Name of the environment

        Returns:
            List of package dictionaries with name and version

        """
        try:
            result = run_command(["conda", "list", "-n", env_name, "--json"], verbose=self.verbose)
            if not is_command_output_str(result):
                return []

            return json.loads(result)
        except Exception as e:
            logger.error(f"Error getting environment packages: {e!s}")
            return []

    def _validate_packages(
        self, env_name: str, packages: list[dict[str, Any]]
    ) -> list[PackageValidationResult]:
        """Validate packages in an environment.

        Args:
            env_name: Name of the environment
            packages: List of package dictionaries

        Returns:
            List of validation results

        """
        results = []

        for pkg in packages:
            name = pkg.get("name", "")
            version = pkg.get("version", "")
            installed = pkg.get("installed", True)

            # Skip certain packages
            if name in ["python", "pip", "setuptools", "wheel"]:
                results.append(
                    PackageValidationResult(
                        name=name,
                        version=version,
                        installed=installed,
                        importable=True,
                    )
                )
                continue

            # Check if package is importable
            importable = False
            import_error = None

            if installed:
                try:
                    # Try to import the package
                    cmd = ["conda", "run", "-n", env_name, "python", "-c", f"import {name}"]
                    result = run_command(cmd, verbose=self.verbose)
                    importable = is_command_output_str(result) and "ImportError" not in result

                    if not importable:
                        import_error = str(result)
                except Exception as e:
                    import_error = str(e)

            results.append(
                PackageValidationResult(
                    name=name,
                    version=version,
                    installed=installed,
                    importable=importable,
                    import_error=import_error,
                )
            )

        return results

    def _compare_environments(self, source_env: str, target_env: str) -> dict[str, Any]:
        """Compare two environments.

        Args:
            source_env: Name of the source environment
            target_env: Name of the target environment

        Returns:
            Comparison details

        """
        try:
            # Get packages from both environments
            source_packages = self._get_environment_packages(source_env)
            target_packages = self._get_environment_packages(target_env)

            # Extract package names and versions
            source_pkgs = {pkg["name"]: pkg.get("version", "") for pkg in source_packages}
            target_pkgs = {pkg["name"]: pkg.get("version", "") for pkg in target_packages}

            # Find differences
            source_only = set(source_pkgs.keys()) - set(target_pkgs.keys())
            target_only = set(target_pkgs.keys()) - set(source_pkgs.keys())
            common = set(source_pkgs.keys()) & set(target_pkgs.keys())

            # Find version differences
            version_diff = {}
            for pkg in common:
                if source_pkgs[pkg] != target_pkgs[pkg]:
                    version_diff[pkg] = {
                        "source": source_pkgs[pkg],
                        "target": target_pkgs[pkg],
                    }

            return {
                "source_only": list(source_only),
                "target_only": list(target_only),
                "version_differences": version_diff,
                "common_packages": len(common),
            }
        except Exception as e:
            logger.error(f"Error comparing environments: {e!s}")
            return {
                "error": str(e),
                "source_only": [],
                "target_only": [],
                "version_differences": {},
                "common_packages": 0,
            }

    def run_validation_script(self, env_name: str, script_path: PathLike) -> ValidationResult:
        """Run a validation script in the environment.

        Args:
            env_name: Name of the environment
            script_path: Path to the validation script

        Returns:
            Validation result

        """
        if not Path(script_path).exists():
            return ValidationResult(
                passed=False,
                message=f"Validation script not found: {script_path}",
                details={"error": "script_not_found"},
            )

        try:
            # Run the script in the environment
            cmd = ["conda", "run", "-n", env_name, "python", str(script_path)]
            result = run_command(cmd, verbose=self.verbose)

            if not is_command_output_str(result):
                return ValidationResult(
                    passed=False,
                    message="Validation script failed to execute",
                    details={"error": "script_execution_failed"},
                )

            # Check for common error patterns
            if "ImportError" in result or "ModuleNotFoundError" in result:
                return ValidationResult(
                    passed=False,
                    message="Validation script failed due to import errors",
                    details={"error": "import_error", "output": result},
                )

            # Assume success if no errors
            return ValidationResult(
                passed=True,
                message="Validation script executed successfully",
                details={"output": result},
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Error running validation script: {e!s}",
                details={"error": str(e)},
            )

    def validate_python_compatibility(self, env_name: str, test_code: str) -> ValidationResult:
        """Validate Python compatibility in the environment.

        Args:
            env_name: Name of the environment
            test_code: Python code to test

        Returns:
            Validation result

        """
        try:
            # Create a temporary file with the test code
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
                f.write(test_code)
                temp_path = f.name

            # Run the test code in the environment
            cmd = ["conda", "run", "-n", env_name, "python", temp_path]
            result = run_command(cmd, verbose=self.verbose)

            # Clean up the temporary file
            Path(temp_path).unlink()

            if not is_command_output_str(result):
                return ValidationResult(
                    passed=False,
                    message="Python compatibility test failed to execute",
                    details={"error": "execution_failed"},
                )

            # Check for errors
            if "SyntaxError" in result or "IndentationError" in result:
                return ValidationResult(
                    passed=False,
                    message="Python compatibility test failed due to syntax errors",
                    details={"error": "syntax_error", "output": result},
                )

            # Assume success if no errors
            return ValidationResult(
                passed=True,
                message="Python compatibility test passed",
                details={"output": result},
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Error running Python compatibility test: {e!s}",
                details={"error": str(e)},
            )
