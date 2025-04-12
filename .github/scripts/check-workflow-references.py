#!/usr/bin/env python
"""
Pre-commit hook to check workflow references.
"""

import os
import re
import sys
from pathlib import Path


def find_available_actions():
    """Find all available composite actions in the repository."""
    actions_dir = Path(".github/actions")
    if not actions_dir.exists():
        return []

    actions = []
    for action_file in actions_dir.glob("**/action.y*ml"):
        # Extract the action name from the path
        action_name = action_file.parent.relative_to(actions_dir)
        actions.append(str(action_name))

    return actions


def check_workflow_references(file_path, available_actions):
    """Check references in a workflow file."""
    print(f"Checking references in {file_path}...")

    try:
        with open(file_path) as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    errors = []

    # Check for composite action references
    action_refs = re.findall(r"uses:\s+\./.github/actions/([a-zA-Z0-9_-]+)", content)
    for ref in action_refs:
        if ref not in available_actions:
            errors.append(f"References non-existent action: {ref}")

    # Check for incorrect reference format
    if re.search(r"uses:\s+\.github/actions/", content):
        errors.append(
            "Uses incorrect action reference format. Use './.github/actions/' instead of '.github/actions/'"
        )

    # Check for workflow calls
    workflow_calls = re.findall(r"uses:\s+\./.github/workflows/([a-zA-Z0-9_-]+)", content)
    for workflow in workflow_calls:
        if not os.path.exists(f".github/workflows/{workflow}"):
            errors.append(f"Calls non-existent workflow: {workflow}")

    # Check for environment variables
    if "ACT_LOCAL_TESTING" in content and "env:" not in content:
        print(
            f"Warning: {file_path} uses ACT_LOCAL_TESTING but doesn't define it in the env section"
        )

    if errors:
        print(f"Errors in {file_path}:")
        for error in errors:
            print(f"  - {error}")
        return False

    print(f"✓ {file_path} has valid references")
    return True


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("No workflow files to check")
        return 0

    files = sys.argv[1:]
    available_actions = find_available_actions()
    errors = 0

    print(f"Available actions: {', '.join(available_actions)}")

    for file in files:
        if not check_workflow_references(file, available_actions):
            errors += 1

    if errors:
        print(f"Found {errors} errors in workflow references")
        return 1

    print("All workflow references are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
