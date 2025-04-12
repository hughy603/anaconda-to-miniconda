#!/usr/bin/env python3
"""
Set up Git hooks for the project.

This script ensures that all necessary pre-commit hooks are installed
and configured correctly, including commit message validation.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], check: bool = True) -> str:
    """Run a command and return its output."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, check=check)
    return result.stdout.strip()


def setup_hooks():
    """Set up Git hooks for the project."""
    # Check if pre-commit is installed
    try:
        run_command(["pre-commit", "--version"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: pre-commit is not installed.")
        print("Please install it with: pip install pre-commit")
        return False

    # Install pre-commit hooks
    print("\nInstalling pre-commit hooks...")
    run_command(["pre-commit", "install"])
    run_command(["pre-commit", "install", "--hook-type", "commit-msg"])
    run_command(["pre-commit", "install", "--hook-type", "pre-push"])

    # Set up commit template
    template_path = Path(".github/commit-template.txt")
    if template_path.exists():
        print("\nSetting up commit template...")
        run_command(["git", "config", "--local", "commit.template", str(template_path)])
        print(f"Commit template set to: {template_path}")
    else:
        print(f"\nWarning: Commit template not found at {template_path}")
        print("Skipping commit template setup.")

    print("\nRunning pre-commit hooks on all files to verify setup...")
    try:
        run_command(["pre-commit", "run", "--all-files"], check=False)
    except subprocess.CalledProcessError:
        print("Some pre-commit checks failed, but hooks are installed correctly.")

    print("\n✅ Git hooks setup complete!")
    print("\nYour commits will now be validated for:")
    print("  - Code quality (linting, formatting, type checking)")
    print("  - Commit message format (Conventional Commits)")
    print(
        "\nValid commit types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
    )
    print("Example: feat: add new feature")
    print("Example: fix(core): resolve issue with parser")

    return True


if __name__ == "__main__":
    if not setup_hooks():
        sys.exit(1)
