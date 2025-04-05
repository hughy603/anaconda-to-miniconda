#!/usr/bin/env python3
"""Dependency management script for uv."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return its output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr}")
        sys.exit(1)


def update_dependencies():
    """Update project dependencies using uv."""
    # Get project root
    project_root = Path(__file__).parent.parent.absolute()

    # Ensure requirements directory exists
    reqs_dir = project_root / "requirements"
    reqs_dir.mkdir(exist_ok=True)

    # Update main requirements
    run_command(
        [
            "uv",
            "pip",
            "compile",
            "pyproject.toml",
            "--output-file",
            "requirements/requirements.txt",
            "--resolution",
            "highest",
        ],
        cwd=project_root,
    )

    # Update dev requirements
    run_command(
        [
            "uv",
            "pip",
            "compile",
            "pyproject.toml",
            "--output-file",
            "requirements/dev-requirements.txt",
            "--extra",
            "dev",
            "--resolution",
            "highest",
        ],
        cwd=project_root,
    )

    # Update test requirements
    run_command(
        [
            "uv",
            "pip",
            "compile",
            "pyproject.toml",
            "--output-file",
            "requirements/test-requirements.txt",
            "--extra",
            "test",
            "--resolution",
            "highest",
        ],
        cwd=project_root,
    )

    # Create combined requirements for CI
    run_command(
        [
            "uv",
            "pip",
            "compile",
            "pyproject.toml",
            "--output-file",
            "requirements/ci-requirements.txt",
            "--extra",
            "dev",
            "--extra",
            "test",
            "--resolution",
            "highest",
        ],
        cwd=project_root,
    )

    print("✅ Dependencies updated successfully!")


if __name__ == "__main__":
    update_dependencies()
