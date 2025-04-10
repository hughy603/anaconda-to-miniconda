#!/usr/bin/env python
"""Template validation script for conda environment validation.

This script can be used as a template for creating custom validation scripts
for your specific environment. It demonstrates how to validate that key
packages are installed and functioning correctly.

Usage:
    conda run -n <environment_name> python validation_script_template.py

Exit codes:
    0: Validation passed
    1: Validation failed
"""

import importlib
import sys


def validate_imports(packages: list[str]) -> tuple[bool, dict[str, str]]:
    """Validate that packages can be imported.

    Args:
        packages: List of package names to validate

    Returns:
        Tuple of (success, errors)

    """
    errors = {}
    success = True

    for package in packages:
        try:
            importlib.import_module(package)
            print(f"✓ Successfully imported {package}")
        except ImportError as e:
            success = False
            errors[package] = str(e)
            print(f"✗ Failed to import {package}: {e}")

    return success, errors


def validate_package_versions(version_checks: dict[str, str]) -> tuple[bool, dict[str, str]]:
    """Validate package versions.

    Args:
        version_checks: Dictionary mapping package names to required versions

    Returns:
        Tuple of (success, errors)

    """
    errors = {}
    success = True

    for package, required_version in version_checks.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", None)

            if version is None:
                # Try alternative version attributes
                for attr in ["version", "VERSION", "release"]:
                    version = getattr(module, attr, None)
                    if version is not None:
                        break

            if version is None:
                errors[package] = "Could not determine version"
                success = False
                print(f"✗ {package}: Could not determine version")
            else:
                print(f"✓ {package}: {version} (required: {required_version})")
                # Simple version comparison - for more complex cases, use packaging.version
                if version != required_version:
                    errors[package] = f"Version mismatch: {version} != {required_version}"
                    success = False
                    print(f"✗ {package}: Version mismatch: {version} != {required_version}")
        except ImportError as e:
            errors[package] = str(e)
            success = False
            print(f"✗ Failed to import {package}: {e}")

    return success, errors


def run_functionality_tests() -> tuple[bool, dict[str, str]]:
    """Run functionality tests for key packages.

    Returns:
        Tuple of (success, errors)

    """
    errors = {}
    success = True

    # Example: Test numpy functionality
    try:
        import numpy as np

        # Create a simple array and perform operations
        arr = np.array([1, 2, 3, 4, 5])
        mean = np.mean(arr)
        std = np.std(arr)
        print(f"✓ NumPy functionality test passed: mean={mean}, std={std}")
    except Exception as e:
        success = False
        errors["numpy_functionality"] = str(e)
        print(f"✗ NumPy functionality test failed: {e}")

    # Example: Test pandas functionality
    try:
        import pandas as pd

        # Create a simple DataFrame and perform operations
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        sum_result = df.sum().sum()
        print(f"✓ Pandas functionality test passed: sum={sum_result}")
    except Exception as e:
        success = False
        errors["pandas_functionality"] = str(e)
        print(f"✗ Pandas functionality test failed: {e}")

    return success, errors


def main() -> int:
    """Run the validation script.

    Returns:
        Exit code (0 for success, 1 for failure)

    """
    print("Starting environment validation...")

    # Define packages to validate
    packages_to_validate = [
        "numpy",
        "pandas",
        "matplotlib",
        "scikit-learn",
        # Add your packages here
    ]

    # Define version requirements
    version_requirements = {
        "numpy": "1.20.0",
        "pandas": "1.3.0",
        # Add your version requirements here
    }

    # Validate imports
    print("\nValidating package imports...")
    import_success, import_errors = validate_imports(packages_to_validate)

    # Validate versions
    print("\nValidating package versions...")
    version_success, version_errors = validate_package_versions(version_requirements)

    # Run functionality tests
    print("\nRunning functionality tests...")
    functionality_success, functionality_errors = run_functionality_tests()

    # Determine overall success
    overall_success = import_success and version_success and functionality_success

    # Print summary
    print("\nValidation Summary:")
    print(f"Import validation: {'PASSED' if import_success else 'FAILED'}")
    print(f"Version validation: {'PASSED' if version_success else 'FAILED'}")
    print(f"Functionality tests: {'PASSED' if functionality_success else 'FAILED'}")
    print(f"Overall validation: {'PASSED' if overall_success else 'FAILED'}")

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
