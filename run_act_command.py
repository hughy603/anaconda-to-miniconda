#!/usr/bin/env python3
"""Run act commands directly with real-time output.

This script allows running act commands directly without going through the
validation framework, showing the output in real-time to help debug issues.
It also provides debugging capabilities to help troubleshoot workflow issues.
"""

import argparse
import json
import os
import random
import string
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def _build_act_command(
    workflow_file: str | Path,
    event_file: str,
    job: str | None = None,
    debug: bool = False,
    verbose: bool = False,
) -> list[str]:
    """Build the act command with appropriate arguments.

    Args:
        workflow_file: The workflow file to run
        event_file: The event file to use
        job: The specific job to run (optional)
        debug: Whether to enable debug mode (default: False)
        verbose: Whether to show verbose output (default: False)

    Returns:
        The command as a list of strings
    """
    cmd = ["act", "-W", workflow_file, "-e", event_file]

    # Add job filter if provided
    if job:
        cmd.extend(["--job", job])

    # Add platform mapping
    cmd.extend(["-P", "ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"])

    # Add cache path
    if os.path.exists("./.act-cache"):
        cmd.extend(["--action-cache-path", "./.act-cache"])

    # Add environment variables
    cmd.extend(["--env", "ACT=true", "--env", "ACT_LOCAL_TESTING=true"])

    # Add debug environment variables if debug mode is enabled
    if debug:
        cmd.extend(["--env", "ACTIONS_STEP_DEBUG=true", "--env", "ACTIONS_RUNNER_DEBUG=true"])

    # Add secrets
    cmd.extend(
        ["-s", "ACT=true", "-s", "ACT_LOCAL_TESTING=true", "-s", "GITHUB_TOKEN=local-testing-token"]
    )

    # Add verbose flag if specified
    if verbose or debug:
        cmd.append("--verbose")

    return cmd


def _execute_process(cmd: list[str], timeout: int) -> int:
    """Execute a process with real-time output and timeout.

    Args:
        cmd: The command to execute as a list of strings
        timeout: Timeout in seconds

    Returns:
        The return code from the process
    """
    try:
        # Run the command with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
        )

        # Print output in real-time
        if process.stdout:
            for line in process.stdout:
                print(line, end="")

        # Wait for the process to complete with timeout
        try:
            return_code = process.wait(timeout=timeout)
            print(f"\nCommand completed with return code: {return_code}")
            return return_code
        except subprocess.TimeoutExpired:
            # Kill the process if it times out
            print(f"\nCommand timed out after {timeout} seconds")
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                    check=False,
                )
            else:
                process.kill()
            return 1

    except Exception as e:
        print(f"Error running command: {e}")
        return 1


def run_act_command(
    workflow_file: str | Path,
    job: str | None = None,
    event_type: str = "push",
    timeout: int = 300,
    verbose: bool = False,
    debug: bool = False,
    step_by_step: bool = False,
) -> int:
    """Run an act command with real-time output and debugging options.

    Args:
        workflow_file: The workflow file to run
        job: The specific job to run (optional)
        event_type: The event type to trigger (default: push)
        timeout: Timeout in seconds (default: 300)
        verbose: Whether to show verbose output (default: False)
        debug: Whether to enable debug mode (default: False)
        step_by_step: Whether to run the workflow step by step (default: False)

    Returns:
        The return code from the act command
    """
    # Normalize paths to use forward slashes
    workflow_file = str(Path(workflow_file)).replace("\\", "/")

    # Prepare event file
    event_file = f".github/events/{event_type}.json"
    event_file = str(Path(event_file)).replace("\\", "/")

    # Ensure event directory exists
    Path(event_file).parent.mkdir(parents=True, exist_ok=True)

    # Create event file if it doesn't exist or if debug mode is enabled (to ensure correct content)
    if not Path(event_file).exists() or debug:
        # Create a more complete event file with branch information
        create_event_file(event_file, event_type, workflow_file)

    # Build and print the command
    cmd = _build_act_command(workflow_file, event_file, job, debug, verbose)
    print(f"Running command: {' '.join(cmd)}")

    # Execute the command
    return_code = _execute_process(cmd, timeout)

    # If the command failed with "Could not find any stages to run", provide helpful tips
    if return_code != 0 and "Could not find any stages to run" in str(cmd):
        print("\nTip: The workflow might not be triggered by the current event type.")
        print(
            f"Try using a different event type: python {sys.argv[0]} {workflow_file} "
            f"--event pull_request"
        )
        print(f"Or specify a job: python {sys.argv[0]} {workflow_file} --job <job_name>")
        print(f"Use --list to see available jobs: python {sys.argv[0]} {workflow_file} --list")

    return return_code


def _get_repo_owner() -> str:
    """Get the repository owner name from git config.

    Returns:
        The owner name, or "owner" if not found
    """
    owner_name = "owner"
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            owner_name = result.stdout.strip()
    except Exception:
        pass
    return owner_name


def _determine_branch_name(workflow_file: str | None = None) -> str:
    """Determine the branch name from git or workflow file.

    Args:
        workflow_file: The workflow file to extract branch info from (optional)

    Returns:
        The branch name, or "main" if not found
    """
    branch_name = "main"
    if not workflow_file:
        return branch_name

    try:
        # Try to get the current branch from git
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            branch_name = result.stdout.strip()

        # If that fails, try to extract from workflow file
        if not branch_name or branch_name == "HEAD":
            with open(workflow_file) as f:
                workflow_content = yaml.safe_load(f)
                if workflow_content and "on" in workflow_content:
                    triggers = workflow_content["on"]
                    if "push" in triggers and "branches" in triggers["push"]:
                        branches = triggers["push"]["branches"]
                        if isinstance(branches, list) and branches:
                            branch_name = branches[0]
    except Exception as e:
        print(f"Warning: Could not extract branch information: {e}")

    return branch_name


def _create_event_data_for_type(
    event_type: str, branch_name: str, owner_name: str, repo_name: str, sha: str
) -> dict:
    """Create event data specific to the event type.

    Args:
        event_type: The event type (e.g., push, pull_request)
        branch_name: The branch name
        owner_name: The repository owner name
        repo_name: The repository name
        sha: The commit SHA

    Returns:
        The event data as a dictionary
    """
    # Basic event data
    event_data = {
        "ref": f"refs/heads/{branch_name}",
        "repository": {
            "name": repo_name,
            "full_name": f"{owner_name}/{repo_name}",
            "owner": {"name": owner_name, "login": owner_name},
        },
        "sender": {
            "login": owner_name,
            "id": 12345,
        },
        "sha": sha,
        "workflow": event_type,
    }

    # Add additional fields based on event type
    if event_type == "push":
        event_data.update(
            {
                "before": "0" * 40,
                "after": sha,
                "created": False,
                "deleted": False,
                "forced": False,
                "head_commit": {
                    "id": sha,
                    "message": "Local test commit",
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )
    elif event_type == "pull_request":
        # Generate another SHA for the head branch
        head_sha = "".join(random.choices(string.hexdigits.lower(), k=40))
        event_data.update(
            {
                "action": "opened",
                "number": 1,
                "pull_request": {
                    "number": 1,
                    "title": "Local test PR",
                    "body": "Testing pull request locally",
                    "head": {"ref": "feature-branch", "sha": head_sha},
                    "base": {"ref": branch_name, "sha": sha},
                    "user": {"login": owner_name},
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
            }
        )
    elif event_type == "schedule":
        # For schedule events
        event_data.update(
            {
                "schedule": "0 0 * * *",
                "event_type": "schedule",
            }
        )
    elif event_type == "release":
        event_data.update(
            {
                "action": "published",
                "release": {
                    "tag_name": "v1.0.0",
                    "name": "v1.0.0",
                    "body": "Local test release",
                    "draft": False,
                    "prerelease": False,
                    "created_at": datetime.now().isoformat(),
                    "published_at": datetime.now().isoformat(),
                },
            }
        )

    return event_data


def create_event_file(
    event_file_path: str, event_type: str, workflow_file: str | None = None
) -> None:
    """Create an event file for act with appropriate content.

    Args:
        event_file_path: Path to the event file to create
        event_type: The event type (e.g., push, pull_request)
        workflow_file: The workflow file to extract trigger information from (optional)
    """
    # Get repository info
    repo_name = Path.cwd().name
    owner_name = _get_repo_owner()

    # Generate a random SHA
    sha = "".join(random.choices(string.hexdigits.lower(), k=40))

    # Determine branch name
    branch_name = _determine_branch_name(workflow_file)

    # Create event data based on event type
    event_data = _create_event_data_for_type(event_type, branch_name, owner_name, repo_name, sha)

    # Write event file
    with open(event_file_path, "w") as f:
        json.dump(event_data, f, indent=4)

    print(f"Created {event_type} event file at {event_file_path} with branch {branch_name}")


def extract_steps_from_workflow(workflow_file: str, job_name: str | None = None) -> list:
    """Extract steps from a workflow file for a specific job.

    Args:
        workflow_file: The workflow file to extract steps from
        job_name: The job to extract steps from (optional)

    Returns:
        A list of steps for the job
    """
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    if not workflow or "jobs" not in workflow:
        print(f"No jobs found in {workflow_file}")
        return []

    # If no job specified, use the first job
    if not job_name:
        job_name = next(iter(workflow["jobs"]))
        print(f"No job specified, using first job: {job_name}")

    # Check if the job exists
    if job_name not in workflow["jobs"]:
        print(f"Job {job_name} not found in {workflow_file}")
        return []

    # Get steps for the job
    steps = workflow["jobs"][job_name].get("steps", [])

    # Add step IDs if not present
    for i, step in enumerate(steps):
        if "id" not in step:
            step["id"] = f"step{i + 1}"

    return steps


def list_workflow_jobs(workflow_file: str) -> None:
    """List all jobs in a workflow file.

    Args:
        workflow_file: The workflow file to list jobs from
    """
    try:
        with open(workflow_file) as f:
            workflow = yaml.safe_load(f)

        if not workflow or "jobs" not in workflow:
            print(f"No jobs found in {workflow_file}")
            return

        print(f"\nJobs in {workflow_file}:")
        for job_id, job_config in workflow["jobs"].items():
            job_name = job_config.get("name", job_id)
            print(f"  - {job_id}: {job_name}")

        # Print trigger information
        if "on" in workflow:
            triggers = workflow["on"]
            print("\nWorkflow triggers:")
            if isinstance(triggers, dict):
                for event, config in triggers.items():
                    if isinstance(config, dict) and "branches" in config:
                        branches = config["branches"]
                        print(f"  - {event} on branches: {', '.join(branches)}")
                    else:
                        print(f"  - {event}")
            else:
                print(f"  - {triggers}")
    except Exception as e:
        print(f"Error listing jobs: {e}")


def run_step_by_step(
    workflow_file: str,
    job: str | None = None,
    event_type: str = "push",
    timeout: int = 300,
    verbose: bool = False,
) -> int:
    """Run a workflow step by step, pausing after each step.

    Args:
        workflow_file: The workflow file to run
        job: The specific job to run (optional)
        event_type: The event type to trigger (default: push)
        timeout: Timeout in seconds (default: 300)
        verbose: Whether to show verbose output (default: False)

    Returns:
        The return code from the last step
    """
    steps = extract_steps_from_workflow(workflow_file, job)

    if not steps:
        print(f"No steps found in {workflow_file}")
        return 1

    print(f"Found {len(steps)} steps in {workflow_file}")

    return_code = 0
    for i, step in enumerate(steps):
        step_id = step.get("id", f"step{i + 1}")
        step_name = step.get("name", step_id)

        print(f"\n{'=' * 80}")
        print(f"Running step {i + 1}/{len(steps)}: {step_name}")
        print(f"{'=' * 80}")

        # Run just this step
        cmd = ["act", "-W", workflow_file, "-e", f".github/events/{event_type}.json"]
        if job:
            cmd.extend(["--job", job])

        # Add step filter
        cmd.extend(["--step", step_id])

        # Add verbose flag if specified
        if verbose:
            cmd.append("--verbose")

        # Run the command
        print(f"Running command: {' '.join(cmd)}")
        return_code = subprocess.call(cmd)

        if return_code != 0:
            print(f"\nStep {step_name} failed with return code {return_code}")
            if input("Continue to next step? (y/n): ").lower() != "y":
                return return_code

        # Pause for inspection
        if i < len(steps) - 1:  # Don't pause after the last step
            input("\nPress Enter to continue to the next step...")

    return return_code


def _inspect_event_files() -> None:
    """Inspect event files and display information about them."""
    event_files = list(Path(".github/events").glob("*.json"))
    if not event_files:
        return

    print("\nEvent Files:")
    for event_file in event_files:
        print(f"  {event_file}")
        try:
            with open(event_file) as f:
                event_data = json.load(f)
                print(f"    Event type: {event_file.stem}")
                if "repository" in event_data:
                    repo = event_data["repository"]
                    print(f"    Repository: {repo.get('full_name', 'N/A')}")
                if "ref" in event_data:
                    print(f"    Ref: {event_data['ref']}")
        except Exception as e:
            print(f"    Error reading event file: {e}")


def _inspect_artifacts() -> None:
    """Inspect workflow artifacts and display information about them."""
    artifact_dirs = list(Path(".").glob(".act_artifacts*"))
    if not artifact_dirs:
        return

    print("\nArtifacts:")
    for artifact_dir in artifact_dirs:
        artifacts = list(artifact_dir.glob("*"))
        for artifact in artifacts:
            print(f"  {artifact.name}")


def _inspect_logs() -> None:
    """Inspect workflow logs and display information about them."""
    log_dirs = list(Path(".").glob(".act_logs*"))
    if not log_dirs:
        return

    print("\nLogs:")
    for log_dir in log_dirs:
        logs = list(log_dir.glob("*"))
        for log in logs:
            print(f"  {log.name}")


def inspect_workflow_state() -> None:
    """Inspect the current state of workflow runs.

    This function looks for .act directories and displays information about
    the most recent workflow runs.
    """
    print("\nInspecting workflow state...")

    # Look for .act directories
    act_dirs = list(Path(".").glob(".act*"))
    if not act_dirs:
        print("No .act directories found. No workflow runs detected.")
        return

    for act_dir in act_dirs:
        print(f"\nExamining {act_dir}...")

        # Inspect different components
        _inspect_event_files()
        _inspect_artifacts()
        _inspect_logs()


def main() -> int:
    """Parse command line arguments and run the act command."""
    parser = argparse.ArgumentParser(
        description="Run act commands with real-time output and debugging options"
    )
    parser.add_argument("workflow_file", nargs="?", help="The workflow file to run")
    parser.add_argument("--job", help="The specific job to run")
    parser.add_argument("--event", default="push", help="The event type to trigger (default: push)")
    parser.add_argument(
        "--timeout", type=int, default=300, help="Timeout in seconds (default: 300)"
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--step-by-step", action="store_true", help="Run workflow step by step")
    parser.add_argument("--inspect", action="store_true", help="Inspect workflow state")
    parser.add_argument("--list", action="store_true", help="List jobs in the workflow")

    args = parser.parse_args()

    # Check if workflow file is provided when required
    if not args.workflow_file and not args.inspect and not args.list:
        parser.error("workflow_file is required unless --inspect is specified")

    # If inspect flag is set, just inspect the workflow state and exit
    if args.inspect:
        inspect_workflow_state()
        return 0

    # If list flag is set, list jobs in the workflow and exit
    if args.list:
        if not args.workflow_file:
            parser.error("workflow_file is required with --list")
        list_workflow_jobs(args.workflow_file)
        return 0

    # If step-by-step flag is set, run the workflow step by step
    if args.step_by_step:
        return run_step_by_step(
            args.workflow_file, args.job, args.event, args.timeout, args.verbose
        )

    # Otherwise, run the workflow normally
    try:
        return run_act_command(
            args.workflow_file, args.job, args.event, args.timeout, args.verbose, args.debug, False
        )
    except Exception as e:
        print(f"Error: {e}")
        print("\nTip: If you're seeing 'Could not find any stages to run', try:")
        print(
            f"  1. Using --list to see available jobs: python {sys.argv[0]} "
            f"{args.workflow_file} --list"
        )
        print(
            f"  2. Specifying a job with --job: python {sys.argv[0]} "
            f"{args.workflow_file} --job <job_name>"
        )
        print(
            f"  3. Using a different event type with --event: python {sys.argv[0]} "
            f"{args.workflow_file} --event pull_request"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
