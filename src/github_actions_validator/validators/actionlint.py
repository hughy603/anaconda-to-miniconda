"""Actionlint validator for GitHub Actions workflows.

This module provides a thin wrapper around the actionlint tool for
validating GitHub Actions workflow syntax.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import ValidationConfig


def validate_syntax(workflow_file: Path, config: ValidationConfig) -> tuple[bool, list[str]]:
    """Validate workflow syntax using actionlint.

    Args:
        workflow_file: The workflow file to validate
        config: The validation configuration

    Returns:
        A tuple of (success, errors)
    """
    errors: list[str] = []

    if config.skip_lint:
        if config.verbose:
            print(f"Skipping actionlint validation for {workflow_file} (skip_lint is set)")
        return True, errors

    # Check if actionlint is installed
    try:
        subprocess.run(["actionlint", "--version"], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        error_msg = (
            "actionlint not found. Please install actionlint: "
            "https://github.com/rhysd/actionlint#installation"
        )
        print(error_msg)
        errors.append(error_msg)
        return False, errors

    # Run actionlint
    try:
        if config.verbose:
            print(f"Running actionlint on {workflow_file}")

        result = subprocess.run(
            ["actionlint", str(workflow_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            # Parse actionlint output for errors
            for line in result.stdout.splitlines() + result.stderr.splitlines():
                if line.strip():
                    errors.append(line)

            if config.verbose:
                print(f"actionlint found {len(errors)} errors in {workflow_file}")

            return False, errors

        if config.verbose:
            print(f"actionlint validation passed for {workflow_file}")

        return True, errors

    except Exception as e:
        error_msg = f"Error running actionlint: {e}"
        print(error_msg)
        errors.append(error_msg)
        return False, errors


def validate_all_syntax(
    workflow_files: list[Path], config: ValidationConfig
) -> tuple[bool, list[str]]:
    """Validate syntax for multiple workflow files.

    Args:
        workflow_files: The workflow files to validate
        config: The validation configuration

    Returns:
        A tuple of (success, errors)
    """
    all_success = True
    all_errors: list[str] = []

    for workflow_file in workflow_files:
        success, errors = validate_syntax(workflow_file, config)

        if not success:
            all_success = False

        all_errors.extend(errors)

    return all_success, all_errors
