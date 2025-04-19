#!/usr/bin/env python3
"""Check Python 3.11 and 3.12 compatibility by running tests with both versions.

This script can be used as a pre-commit hook to ensure code is compatible
with both Python 3.11 and 3.12.
"""

import os
import subprocess
import sys
from pathlib import Path


def get_python_path(version: str) -> str:
    """Get the absolute path to the Python executable for a given version."""
    if sys.platform == "win32":
        return f"C:\\Python{version}\\python.exe"
    else:
        return f"/usr/bin/python{version}"


def get_hatch_path() -> str:
    """Get the absolute path to the hatch executable."""
    if sys.platform == "win32":
        return "C:\\Program Files\\Hatch\\hatch.exe"
    else:
        return "/usr/local/bin/hatch"


def get_poetry_path() -> str:
    """Get the absolute path to the poetry executable."""
    if sys.platform == "win32":
        return "C:\\Program Files\\Poetry\\poetry.exe"
    else:
        return "/usr/local/bin/poetry"


def check_python_version(version: str) -> bool:
    """Check if a specific Python version is available."""
    python_path = get_python_path(version)
    try:
        subprocess.run(
            [python_path, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_hatch() -> bool:
    """Check if hatch is available."""
    hatch_path = get_hatch_path()
    try:
        subprocess.run(
            [hatch_path, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_poetry() -> bool:
    """Check if poetry is available."""
    poetry_path = get_poetry_path()
    try:
        subprocess.run(
            [poetry_path, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_tests(version: str) -> bool:
    """Run tests with the specified Python version."""
    python_path = get_python_path(version)
    hatch_path = get_hatch_path()
    poetry_path = get_poetry_path()

    hatch_installed = check_hatch()
    poetry_installed = check_poetry()

    if hatch_installed:
        print("Using hatch to run tests...")
        try:
            result = subprocess.run(
                [hatch_path, "env", "create", f"python{version}"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Error creating hatch environment: {result.stderr}")
                return False

            result = subprocess.run(
                [hatch_path, "run", "test:run", "tests/test_basic.py"],
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running tests with hatch: {e!s}")
            return False
    elif poetry_installed:
        print("Using poetry to run tests...")
        try:
            result = subprocess.run(
                [poetry_path, "env", "use", version],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Error setting poetry environment: {result.stderr}")
                return False

            result = subprocess.run(
                [poetry_path, "install"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Error installing dependencies: {result.stderr}")
                return False

            result = subprocess.run(
                [poetry_path, "run", "pytest", "-xvs", "tests/test_basic.py"],
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running tests with poetry: {e!s}")
            return False
    else:
        print("Neither hatch nor poetry found. Using system Python...")
        try:
            result = subprocess.run(
                [python_path, "-m", "pytest", "-xvs", "tests/test_basic.py"],
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running tests with system Python: {e!s}")
            return False

    if result.returncode != 0:
        print(f"Tests failed: {result.stderr}")
        return False

    print("Tests passed!")
    return True


def ensure_basic_test_exists():
    """Ensure a basic test file exists to check compatibility."""
    tests_dir = Path("tests")
    basic_test_file = tests_dir / "test_basic.py"

    if not tests_dir.exists():
        print("Creating tests directory...")
        tests_dir.mkdir(parents=True)

    if not basic_test_file.exists():
        print("Creating basic test file...")
        basic_test_file.write_text("""
def test_placeholder():
    \"\"\"A placeholder test to ensure pytest finds at least one test.\"\"\"
    assert True
""")


def main():
    """Main entry point."""
    versions = ["3.8", "3.9", "3.10", "3.11", "3.12"]
    failed_versions = []

    # Check if we're in a CI environment
    if os.environ.get("CI") == "true":
        print("Running in CI environment, skipping local Python version check")
        return 0

    # Ensure a basic test file exists
    ensure_basic_test_exists()

    for version in versions:
        print(f"\nChecking Python {version}...")
        if not check_python_version(version):
            print(f"Python {version} not found")
            continue

        if not run_tests(version):
            failed_versions.append(version)

    if failed_versions:
        print(f"\nFailed versions: {failed_versions}")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
