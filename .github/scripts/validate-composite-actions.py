#!/usr/bin/env python
"""
Pre-commit hook to validate GitHub Actions composite actions.
"""

import sys

import yaml


def validate_action_file(file_path):
    """Validate a GitHub Actions composite action file."""
    print(f"Validating {file_path}...")

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


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("No action files to check")
        return 0

    files = sys.argv[1:]
    errors = 0

    for file in files:
        if not validate_action_file(file):
            errors += 1

    if errors:
        print(f"Found {errors} errors in action files")
        return 1

    print("All action files are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
