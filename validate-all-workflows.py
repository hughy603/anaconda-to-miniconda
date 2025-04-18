#!/usr/bin/env python3
"""Validate all GitHub Actions workflows by running them locally.

This script is a direct replacement for validate-all-workflows.ps1, providing
the same functionality but with improved error handling and reporting.
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to the path so we can import the package
sys.path.append(str(Path(__file__).parent / "src"))

import importlib.util

from github_actions_validator.config import ValidationConfig
from github_actions_validator.discovery import find_workflows
from github_actions_validator.logging import configure_logging, get_log_file_path, logger
from github_actions_validator.validators.execution import validate_all_execution

# Check if rich is available
RICH_AVAILABLE = importlib.util.find_spec("rich") is not None


def main() -> int:
    """Validate all GitHub Actions workflows."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Validate GitHub Actions workflows locally.")
    parser.add_argument(
        "--changed-only", action="store_true", help="Only validate workflows that have changed"
    )
    parser.add_argument("--parallel", action="store_true", help="Run validations in parallel")
    parser.add_argument(
        "--max-parallel", type=int, default=3, help="Maximum number of parallel jobs"
    )
    parser.add_argument(
        "--secrets-file", default=".github/local-secrets.json", help="Path to secrets file"
    )
    parser.add_argument("--cache-path", default="./.act-cache", help="Path to cache directory")
    parser.add_argument("--custom-image", default="", help="Use custom Docker image")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--dry-run", action="store_true", help="List workflows without running them"
    )
    parser.add_argument("--skip-lint", action="store_true", help="Skip actionlint validation")
    parser.add_argument("--default-event", default="push", help="Default event type")
    parser.add_argument("--workflow-file", default="", help="Specific workflow file to validate")
    parser.add_argument(
        "--job-timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each job (default: 300)",
    )

    args = parser.parse_args()

    # Create a Rich console if available (for future use)
    # console = Console() if RICH_AVAILABLE else None

    # Create an error reporter (for future use)
    # error_reporter = ErrorReporter(console)

    # Create configuration
    config = ValidationConfig.create(
        None,  # config_file
        changed_only=args.changed_only,
        secrets_file=args.secrets_file,
        cache_path=args.cache_path,
        custom_image=args.custom_image,
        verbose=args.verbose,
        dry_run=args.dry_run,
        skip_lint=args.skip_lint,
        default_event=args.default_event,
        job_timeout=args.job_timeout,
        workflow_file=args.workflow_file,
    )

    # Config is already set up with workflow_file

    # Configure logging
    log_file = get_log_file_path()
    configure_logging(
        level="DEBUG" if config.verbose else "INFO", log_file=log_file, verbose=config.verbose
    )

    logger.info("Starting GitHub Actions workflow validation")
    logger.debug(
        "Configuration: %s",
        {
            "changed_only": config.changed_only,
            "verbose": config.verbose,
            "dry_run": config.dry_run,
            "skip_lint": config.skip_lint,
            "default_event": config.default_event,
            "workflow_file": config.workflow_file,
            "job_timeout": config.job_timeout,
        },
    )

    try:
        # Find workflows to validate
        if config.workflow_file:
            workflow_files = find_workflows(workflow_file=config.workflow_file)
            print(f"Validating specific workflow: {config.workflow_file}")
        elif config.changed_only:
            print("Identifying changed workflows...")
            workflow_files = find_workflows(changed_only=True)
            print(f"Found {len(workflow_files)} changed workflow files.")
        else:
            print("Identifying all workflows...")
            workflow_files = find_workflows()
            print(f"Found {len(workflow_files)} workflow files.")

        if not workflow_files:
            print("No workflows to validate.")
            return 0

        # If dry run is specified, just list the workflows
        if config.dry_run:
            print("\nDry run mode - would validate these workflows:")
            for workflow_file in workflow_files:
                print(f"  - {workflow_file.name}")
            print("\nDry run completed successfully.")
            return 0

        # Validate workflows
        print("\nStep 1: Validating workflow syntax with actionlint...")
        if config.skip_lint:
            print("Skipping actionlint validation (skip_lint flag is set)...")

        print("\nStep 2: Running workflows in local containers with act...")

        # Validate workflows
        success, errors = validate_all_execution(workflow_files, config)

        # Print summary
        if success:
            print("\n✅ All workflows validated successfully!")
        else:
            print("\n❌ One or more workflows failed validation.")

        return 0 if success else 1

    except Exception as e:
        print(f"Error: {e!s}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
