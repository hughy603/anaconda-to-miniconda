"""Workflow discovery for GitHub Actions validation.

This module provides functions for discovering GitHub Actions workflow files.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def find_workflows(
    workflow_file: str | None = None,
    changed_only: bool = False,
    workflows_dir: str = ".github/workflows",
) -> list[Path]:
    """Find GitHub Actions workflow files.

    Args:
        workflow_file: Specific workflow file to find (optional)
        changed_only: Only find workflows that have changed (default: False)
        workflows_dir: Directory containing workflow files (default: .github/workflows)

    Returns:
        A list of workflow file paths
    """
    if workflow_file:
        # Find specific workflow file
        path = Path(workflow_file)
        if path.exists():
            return [path]

        # Try with workflows directory prefix
        path = Path(workflows_dir) / workflow_file
        if path.exists():
            return [path]

        print(f"Warning: Workflow file not found: {workflow_file}")
        return []

    # Find all workflow files
    workflows_path = Path(workflows_dir)
    if not workflows_path.exists() or not workflows_path.is_dir():
        print(f"Warning: Workflows directory not found: {workflows_dir}")
        return []

    # Get all YAML files in the workflows directory
    workflow_files = list(workflows_path.glob("*.yml")) + list(workflows_path.glob("*.yaml"))

    if changed_only:
        # Find changed files using git
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )

            changed_files = set(result.stdout.splitlines())

            # Filter workflow files to only include changed files
            workflow_files = [
                wf
                for wf in workflow_files
                if str(wf) in changed_files or str(wf).replace("\\", "/") in changed_files
            ]
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Warning: Could not determine changed files. Using all workflow files.")

    return sorted(workflow_files)


def extract_jobs(workflow_file: Path) -> list[str]:
    """Extract job IDs from a workflow file.

    Args:
        workflow_file: Path to the workflow file

    Returns:
        A list of job IDs
    """
    try:
        import yaml

        with open(workflow_file) as f:
            workflow = yaml.safe_load(f)

        if not workflow or not isinstance(workflow, dict):
            return []

        jobs = workflow.get("jobs", {})
        if not jobs or not isinstance(jobs, dict):
            return []

        return list(jobs.keys())

    except (ImportError, yaml.YAMLError, FileNotFoundError):
        return []
