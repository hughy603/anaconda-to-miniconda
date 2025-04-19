#!/usr/bin/env python
"""Example script demonstrating the validation framework."""

import argparse
import json
import sys
from pathlib import Path

from conda_forge_converter.validation import ValidationFramework


def main() -> int:  # noqa: C901
    """Run the validation example."""
    parser = argparse.ArgumentParser(description="Validate a converted conda environment")
    parser.add_argument("env_name", help="Name of the environment to validate")
    parser.add_argument("--source-env", help="Name of the source environment for comparison")
    parser.add_argument("--script", help="Path to a validation script to run")
    parser.add_argument("--output", help="Path to save validation results as JSON")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Create validation framework
    framework = ValidationFramework(verbose=args.verbose)

    # Validate the environment
    result = framework.validate_environment(args.env_name, args.source_env)

    # Print validation results
    print(f"\nValidation {'PASSED' if result.passed else 'FAILED'}")
    print(f"Message: {result.message}")

    # Print package details
    if "package_results" in result.details:
        print("\nPackage Validation Results:")
        for pkg in result.details["package_results"]:
            status = "✓" if pkg["installed"] and pkg["importable"] else "✗"
            print(f"{status} {pkg['name']} {pkg['version'] or ''}")
            if not pkg["installed"]:
                print("  - Not installed")
            elif not pkg["importable"]:
                print(f"  - Import error: {pkg['import_error']}")

    # Print comparison details if available
    if "comparison" in result.details:
        comparison = result.details["comparison"]
        print("\nEnvironment Comparison:")
        print(f"Common packages: {comparison['common_packages']}")

        if comparison["source_only"]:
            print("\nPackages only in source environment:")
            for pkg in comparison["source_only"]:
                print(f"  - {pkg}")

        if comparison["target_only"]:
            print("\nPackages only in target environment:")
            for pkg in comparison["target_only"]:
                print(f"  - {pkg}")

        if comparison["version_differences"]:
            print("\nVersion differences:")
            for pkg, versions in comparison["version_differences"].items():
                print(f"  - {pkg}: {versions['source']} -> {versions['target']}")

    # Run validation script if provided
    if args.script:
        script_path = Path(args.script)
        if not script_path.exists():
            print(f"\nError: Validation script not found: {script_path}")
            return 1

        print(f"\nRunning validation script: {script_path}")
        script_result = framework.run_validation_script(args.env_name, script_path)
        print(f"Script validation {'PASSED' if script_result.passed else 'FAILED'}")
        print(f"Message: {script_result.message}")

        if not script_result.passed and "output" in script_result.details:
            print("\nScript output:")
            print(script_result.details["output"])

    # Save results to file if requested
    if args.output:
        output_path = Path(args.output)
        with output_path.open("w") as f:
            # Convert result to dict for JSON serialization
            result_dict = {
                "passed": result.passed,
                "message": result.message,
                "details": result.details,
            }
            json.dump(result_dict, f, indent=2)
        print(f"\nValidation results saved to: {output_path}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
