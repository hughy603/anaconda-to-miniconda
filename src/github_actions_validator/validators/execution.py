"""Execution validator for GitHub Actions workflows.

This module provides a thin wrapper around the act tool for
running GitHub Actions workflows locally.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from ..config import ValidationConfig


def prepare_event_file(event_type: str, workflow_file: Path | None = None) -> Path:
    """Prepare event file for act.

    Args:
        event_type: The event type (e.g., push, pull_request)
        workflow_file: The workflow file to extract branch info from (optional)

    Returns:
        The path to the event file
    """
    event_file = Path(f".github/events/{event_type}.json")

    # Create event directory if it doesn't exist
    event_file.parent.mkdir(parents=True, exist_ok=True)

    # Create event file if it doesn't exist
    if not event_file.exists():
        # Basic event data
        event_data = {
            "ref": "refs/heads/master",
            "repository": {
                "name": Path.cwd().name,
                "full_name": f"owner/{Path.cwd().name}",
                "owner": {"name": "owner"},
            },
        }

        # Write event file
        with open(event_file, "w") as f:
            json.dump(event_data, f, indent=2)

    return event_file


def build_act_command(
    workflow_file: Path,
    config: ValidationConfig,
    event_type: str | None = None,
    job: str | None = None,
) -> list[str]:
    """Build the act command with appropriate arguments.

    Args:
        workflow_file: The workflow file to run
        config: The validation configuration
        event_type: The event type to trigger (default: from config)
        job: The specific job to run (optional)

    Returns:
        The command as a list of strings
    """
    # Determine event type
    if not event_type:
        # Get event type from workflow events mapping
        event_type = config.workflow_events.get(
            workflow_file.name, config.workflow_events.get("*", "push")
        )

    # Prepare event file
    event_file = prepare_event_file(event_type, workflow_file)

    # Normalize paths to use forward slashes
    workflow_file_str = str(workflow_file).replace("\\", "/")
    event_file_str = str(event_file).replace("\\", "/")

    # Build command
    cmd = ["act", "-W", workflow_file_str, "-e", event_file_str]

    # Add job filter if provided
    if job:
        cmd.extend(["--job", job])

    # Add platform mapping
    cmd.extend(["-P", "ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"])

    # Add cache path
    if os.path.exists(config.cache_path):
        cmd.extend(["--action-cache-path", config.cache_path])

    # Add environment variables
    cmd.extend(["--env", "ACT=true", "--env", "ACT_LOCAL_TESTING=true"])

    # Add secrets
    cmd.extend(
        ["-s", "ACT=true", "-s", "ACT_LOCAL_TESTING=true", "-s", "GITHUB_TOKEN=local-testing-token"]
    )

    # Add custom image if specified
    if config.custom_image:
        cmd.extend(["-P", config.custom_image])

    # Add verbose flag if specified
    if config.verbose:
        cmd.append("--verbose")

    return cmd


def validate_execution(
    workflow_file: Path, config: ValidationConfig, job: str | None = None
) -> tuple[bool, list[str]]:
    """Validate workflow execution using act.

    Args:
        workflow_file: The workflow file to validate
        config: The validation configuration
        job: The specific job to validate (optional)

    Returns:
        A tuple of (success, errors)
    """
    errors: list[str] = []

    # Check if act is installed
    try:
        subprocess.run(["act", "--version"], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        error_msg = "act not found. Please install act: https://github.com/nektos/act#installation"
        print(error_msg)
        errors.append(error_msg)
        return False, errors

    # Build command
    cmd = build_act_command(workflow_file, config, job=job)

    if config.verbose:
        print(f"Running command: {' '.join(cmd)}")

    # Run command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=config.job_timeout,
        )

        if result.returncode != 0:
            # Parse output for errors
            for line in result.stdout.splitlines() + result.stderr.splitlines():
                if line.strip() and ("error:" in line.lower() or "failed" in line.lower()):
                    errors.append(line)

            if not errors:
                # If no specific errors found, add the general error
                errors.append(f"act failed with return code {result.returncode}")

            if config.verbose:
                print(f"act found {len(errors)} errors in {workflow_file}")

            return False, errors

        if config.verbose:
            print(f"act validation passed for {workflow_file}")

        return True, errors

    except subprocess.TimeoutExpired:
        error_msg = f"act timed out after {config.job_timeout} seconds"
        print(error_msg)
        errors.append(error_msg)
        return False, errors

    except Exception as e:
        error_msg = f"Error running act: {e}"
        print(error_msg)
        errors.append(error_msg)
        return False, errors


def validate_all_execution(
    workflow_files: list[Path], config: ValidationConfig
) -> tuple[bool, list[str]]:
    """Validate execution for multiple workflow files.

    Args:
        workflow_files: The workflow files to validate
        config: The validation configuration

    Returns:
        A tuple of (success, errors)
    """
    all_success = True
    all_errors: list[str] = []

    for workflow_file in workflow_files:
        success, errors = validate_execution(workflow_file, config)

        if not success:
            all_success = False

        all_errors.extend(errors)

    return all_success, all_errors
