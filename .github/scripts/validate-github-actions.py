#!/usr/bin/env python
"""
Pre-commit hook to validate GitHub Actions workflows and composite actions.
This script combines and simplifies the functionality of:
- validate-composite-actions.py
- check-workflow-references.py
"""

import os
import re
import sys
from pathlib import Path

import yaml


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


def validate_composite_action(file_path):
    """Validate a GitHub Actions composite action file."""
    print(f"Validating composite action: {file_path}")

    try:
        with open(file_path) as f:
            action = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {file_path}")
        print(f"  {e}")
        return False

    # Check for required fields
    errors = []

    if "name" not in action:
        errors.append("Missing 'name' field")

    if "description" not in action:
        errors.append("Missing 'description' field")

    if "runs" not in action:
        errors.append("Missing 'runs' field")
    elif "using" not in action["runs"]:
        errors.append("Missing 'using' field in 'runs'")
    elif action["runs"]["using"] == "composite":
        if "steps" not in action["runs"]:
            errors.append("Missing 'steps' field in 'runs'")
        else:
            # Check steps for shell specification
            for i, step in enumerate(action["runs"]["steps"]):
                if "run" in step and "shell" not in step:
                    step_name = step.get("name", f"step {i + 1}")
                    errors.append(
                        f"Step '{step_name}' with 'run' command is missing 'shell' specification"
                    )

    # Check inputs documentation
    if "inputs" in action:
        for input_name, input_data in action["inputs"].items():
            if "description" not in input_data:
                errors.append(f"Input '{input_name}' is missing 'description'")
            if "required" not in input_data:
                print(f"Warning: Input '{input_name}' should specify if it is required")

    if errors:
        print(f"Errors in {file_path}:")
        for error in errors:
            print(f"  - {error}")
        return False

    print(f"✓ {file_path} is valid")
    return True


def validate_workflow(file_path, available_actions):
    """Validate a GitHub Actions workflow file."""
    print(f"Validating workflow: {file_path}")

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
        print("No files to check")
        return 0

    files = sys.argv[1:]
    available_actions = find_available_actions()
    errors = 0

    print(f"Available actions: {', '.join(available_actions)}")

    for file in files:
        if "actions" in file and file.endswith(("action.yml", "action.yaml")):
            if not validate_composite_action(file):
                errors += 1
        elif "workflows" in file and file.endswith((".yml", ".yaml")):
            if not validate_workflow(file, available_actions):
                errors += 1
        else:
            print(f"Skipping {file} - not a recognized GitHub Actions file")

    if errors:
        print(f"Found {errors} errors in GitHub Actions files")
        return 1

    print("All GitHub Actions files are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())