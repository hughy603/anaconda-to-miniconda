#!/usr/bin/env python
"""
Script to update the coverage threshold in .coveragerc based on current coverage.

This script reads the current coverage from the coverage.xml file and updates
the fail_under threshold in .coveragerc to a slightly higher value. This encourages
gradual improvement of test coverage over time.

Usage:
    python scripts/update_coverage_threshold.py [--increment PERCENT]

Options:
    --increment PERCENT    Amount to increment the threshold by (default: 1.0)
"""

import argparse
import configparser
import re
import sys
import xml.etree.ElementTree as ET


def get_current_coverage():
    """Get the current coverage percentage from coverage.xml."""
    try:
        tree = ET.parse("coverage.xml")
        root = tree.getroot()
        coverage = root.get("line-rate")
        if coverage:
            return float(coverage) * 100
    except (ET.ParseError, FileNotFoundError):
        print("Error: Could not parse coverage.xml. Run tests with coverage first.")
        sys.exit(1)

    return None


def get_current_threshold():
    """Get the current fail_under threshold from .coveragerc."""
    config = configparser.ConfigParser()
    config.read(".coveragerc")

    try:
        return float(config["report"]["fail_under"])
    except (KeyError, ValueError):
        print("Error: Could not find fail_under in .coveragerc")
        return None


def update_threshold(new_threshold: float):
    """Update the fail_under threshold in .coveragerc."""
    # Read the file content
    with open(".coveragerc") as f:
        content = f.read()

    # Replace the fail_under value
    pattern = r"(fail_under\s*=\s*)(\d+(\.\d+)?)"
    new_content = re.sub(pattern, f"\\1{new_threshold:.2f}", content)

    # Write the updated content
    with open(".coveragerc", "w") as f:
        f.write(new_content)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Update coverage threshold")
    parser.add_argument(
        "--increment",
        type=float,
        default=1.0,
        help="Amount to increment the threshold by (default: 1.0)",
    )
    args = parser.parse_args()

    current_coverage = get_current_coverage()
    if current_coverage is None:
        print("Error: Could not determine current coverage")
        sys.exit(1)

    current_threshold = get_current_threshold()
    if current_threshold is None:
        print("Error: Could not determine current threshold")
        sys.exit(1)

    # Calculate new threshold (round to 2 decimal places)
    # If current coverage is already higher than threshold, increment from current coverage
    # Otherwise, increment from current threshold
    base = max(current_coverage, current_threshold)
    new_threshold = round(base + args.increment, 2)

    update_threshold(new_threshold)

    print(f"Current coverage: {current_coverage:.2f}%")
    print(f"Previous threshold: {current_threshold:.2f}%")
    print(f"New threshold: {new_threshold:.2f}%")


if __name__ == "__main__":
    main()
