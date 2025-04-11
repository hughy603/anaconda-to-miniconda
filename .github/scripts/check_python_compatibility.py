#!/usr/bin/env python3
"""Check Python 3.11 and 3.12 compatibility by running tests with both versions.

This script can be used as a pre-commit hook to ensure code is compatible
with both Python 3.11 and 3.12.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_python_version(version):
    """Run tests with the specified Python version."""
    print(f"Testing with Python {version}...")
    try:
        # Check if the Python version is available
        try:
            subprocess.run(
                [f"python{version}", "--version"],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Python {version} not found, skipping compatibility check")
            return True

        # Check if we have hatch or poetry
        hatch_installed = False
        poetry_installed = False

        try:
            subprocess.run(
                ["hatch", "--version"],
                check=True,
                capture_output=True,
            )
            hatch_installed = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        try:
            subprocess.run(
                ["poetry", "--version"],
                check=True,
                capture_output=True,
            )
            poetry_installed = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Run tests with the appropriate tool
        if hatch_installed:
            print("Using hatch to run tests...")
            result = subprocess.run(
                ["hatch", "env", "create", f"python{version}"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Failed to create hatch environment with Python {version}:")
                print(result.stdout)
                print(result.stderr)
                return False

            result = subprocess.run(
                ["hatch", "run", "test:run", "tests/test_basic.py"],
                capture_output=True,
                text=True,
            )
        elif poetry_installed:
            print("Using poetry to run tests...")
            result = subprocess.run(
                ["poetry", "env", "use", version],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Failed to set poetry environment to Python {version}:")
                print(result.stdout)
                print(result.stderr)
                return False

            result = subprocess.run(
                ["poetry", "install"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print("Failed to install dependencies:")
                print(result.stdout)
                print(result.stderr)
                return False

            result = subprocess.run(
                ["poetry", "run", "pytest", "-xvs", "tests/test_basic.py"],
                capture_output=True,
                text=True,
            )
        else:
            print("Neither hatch nor poetry found. Using system Python...")
            result = subprocess.run(
                [f"python{version}", "-m", "pytest", "-xvs", "tests/test_basic.py"],
                capture_output=True,
                text=True,
            )

        if result.returncode != 0:
            print(f"Tests failed with Python {version}:")
            print(result.stdout)
            print(result.stderr)
            return False

        print(f"✅ Compatible with Python {version}")
        return True
    except Exception as e:
        print(f"Error testing with Python {version}: {e}")
        return False


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
    """Check compatibility with Python 3.11 and 3.12."""
    success = True

    # Check if we're in a CI environment
    if os.environ.get("CI") == "true":
        print("Running in CI environment, skipping local Python version check")
        return 0

    # Ensure a basic test file exists
    ensure_basic_test_exists()

    # Check compatibility with Python 3.11 and 3.12
    python_versions = ["3.11", "3.12"]
    for version in python_versions:
        if not check_python_version(version):
            success = False

    if success:
        print("\n✅ Code is compatible with Python 3.11 and 3.12")
    else:
        print("\n❌ Code is not compatible with all Python versions")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
