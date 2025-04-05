"""Command-line interface for the conda-forge-converter package."""

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime

from .core import (
    convert_environment,
    convert_multiple_environments,
    is_conda_environment,
    list_all_conda_environments,
)
from .health import check_environment_health, verify_environment
from .incremental import detect_drift, update_conda_forge_environment
from .reporting import generate_conversion_report, generate_summary_report, print_report_summary
from .utils import logger, setup_logging


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
    ----
        args: Command-line arguments to parse. If None, sys.argv[1:] is used.

    Returns:
    -------
        Parsed arguments as a Namespace object.

    """
    parser = argparse.ArgumentParser(
        description="Convert Anaconda environments to conda-forge environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add subparsers
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Help command
    help_parser = subparsers.add_parser(
        "help", help="Show detailed help with examples and workflows"
    )
    help_parser.add_argument(
        "topic",
        nargs="?",
        choices=["basic", "batch", "advanced", "examples", "health", "report", "update"],
        help="Help topic to display",
    )

    # Health check command
    health_parser = subparsers.add_parser("health", help="Check the health of a conda environment")
    health_parser.add_argument("environment", help="Name of the environment to check")
    health_parser.add_argument(
        "--verify", action="store_true", help="Verify environment functionality by running tests"
    )
    health_parser.add_argument("--output", help="Path to save health check results (JSON format)")

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate a detailed report about a conversion"
    )
    report_parser.add_argument("--source", required=True, help="Source environment name")
    report_parser.add_argument("--target", required=True, help="Target environment name")
    report_parser.add_argument(
        "--output", required=True, help="Path to save report (JSON or YAML format)"
    )
    report_parser.add_argument("--print", action="store_true", help="Print a summary of the report")

    # Update command
    update_parser = subparsers.add_parser(
        "update", help="Update an existing conda-forge environment"
    )
    update_parser.add_argument("environment", help="Name of the conda-forge environment to update")
    update_parser.add_argument("--all", action="store_true", help="Update all outdated packages")
    update_parser.add_argument(
        "--add-missing",
        action="store_true",
        help="Add packages that exist in source but not in target",
    )
    update_parser.add_argument("--packages", nargs="+", help="Specific packages to update")
    update_parser.add_argument("--report", help="Path to save update report (JSON format)")
    update_parser.add_argument(
        "--drift", action="store_true", help="Only detect drift without updating"
    )

    # Single environment options
    parser.add_argument("-s", "--source-env", help="Name of the source Anaconda environment")
    parser.add_argument("-t", "--target-env", help="Name for the new conda-forge environment")

    # Batch conversion options
    parser.add_argument("--batch", action="store_true", help="Convert multiple environments")
    parser.add_argument("--pattern", help="Pattern for matching environment names (e.g., 'data*')")
    parser.add_argument("--exclude", help="Comma-separated list of environments to exclude")
    parser.add_argument(
        "--target-suffix",
        default="_forge",
        help="Suffix to add to target environment names in batch mode (default: _forge)",
    )

    # Environment search paths
    parser.add_argument(
        "--search-path",
        action="append",
        metavar="PATH",
        help="Path to search for conda environments (can be specified multiple times)",
    )
    parser.add_argument(
        "--search-depth",
        type=int,
        default=3,
        help="Maximum directory depth when searching for environments (default: 3)",
    )

    # Performance and resource options
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=1,
        help="Maximum number of parallel conversions (default: 1)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backing up environment specifications",
    )

    # Python version
    parser.add_argument("--python", help="Specify Python version for the new environment")

    # Output control
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be installed without creating environments",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output of conda commands",
    )
    parser.add_argument("--log-file", help="Path to log file for detailed logging")

    # Reporting options for standard conversion
    parser.add_argument(
        "--generate-report",
        help="Path to save conversion report (JSON or YAML format)",
    )

    # Health check options for standard conversion
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health check on environments before and after conversion",
    )

    # Post-conversion verification
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify target environment functionality after conversion",
    )

    return parser.parse_args(args)


def show_help(topic: str | None = None) -> None:
    """Show detailed help on a specific topic.

    Args:
        topic: The help topic to display

    """
    if topic == "basic" or topic is None:
        print("\n=== Basic Usage ===")
        print("\nConverting a single environment:")
        print("  conda-forge-converter -s myenv -t myenv_forge")
        print("\nTo specify a Python version:")
        print("  conda-forge-converter -s myenv -t myenv_forge --python 3.9")
        print("\nTo preview without creating:")
        print("  conda-forge-converter -s myenv -t myenv_forge --dry-run")

    if topic == "batch" or topic is None:
        print("\n=== Batch Conversion ===")
        print("\nConvert all environments:")
        print("  conda-forge-converter --batch")
        print("\nFilter environments by pattern:")
        print("  conda-forge-converter --batch --pattern 'data*'")
        print("\nExclude specific environments:")
        print("  conda-forge-converter --batch --exclude 'test_env,dev_env'")
        print("\nSet custom target suffix:")
        print("  conda-forge-converter --batch --target-suffix '_cf'")

    if topic == "advanced" or topic is None:
        print("\n=== Advanced Options ===")
        print("\nParallel conversion:")
        print("  conda-forge-converter --batch --max-parallel 4")
        print("\nSearch custom paths:")
        print(
            "  conda-forge-converter --batch --search-path /opt/conda_envs --search-path ~/custom_envs"
        )
        print("\nSkip backup:")
        print("  conda-forge-converter --batch --no-backup")
        print("\nDetailed logging:")
        print("  conda-forge-converter -s myenv -t myenv_forge --verbose --log-file conversion.log")

    if topic == "health" or topic is None:
        print("\n=== Health Check ===")
        print("\nCheck environment health:")
        print("  conda-forge-converter health myenv")
        print("\nVerify environment functionality:")
        print("  conda-forge-converter health myenv --verify")
        print("\nSave health report to file:")
        print("  conda-forge-converter health myenv --output health_report.json")
        print("\nInclude health check during conversion:")
        print("  conda-forge-converter -s myenv -t myenv_forge --health-check")

    if topic == "report" or topic is None:
        print("\n=== Reporting ===")
        print("\nGenerate conversion report:")
        print(
            "  conda-forge-converter report --source myenv --target myenv_forge --output report.json"
        )
        print("\nPrint report summary:")
        print(
            "  conda-forge-converter report --source myenv --target myenv_forge --output report.json --print"
        )
        print("\nGenerate report during conversion:")
        print("  conda-forge-converter -s myenv -t myenv_forge --generate-report report.json")

    if topic == "update" or topic is None:
        print("\n=== Incremental Updates ===")
        print("\nDetect drift between environments:")
        print("  conda-forge-converter update myenv_forge --drift")
        print("\nUpdate all outdated packages:")
        print("  conda-forge-converter update myenv_forge --all")
        print("\nUpdate specific packages:")
        print("  conda-forge-converter update myenv_forge --packages numpy pandas matplotlib")
        print("\nAdd missing packages from source:")
        print("  conda-forge-converter update myenv_forge --add-missing")
        print("\nSave update report:")
        print("  conda-forge-converter update myenv_forge --all --report update_report.json")

    if topic == "examples" or topic is None:
        print("\n=== Common Examples ===")
        print("\nExample 1: Convert a specific data science environment")
        print("  conda-forge-converter -s data_science -t data_science_forge")
        print("\nExample 2: Convert all environments with 'ml' in their name")
        print("  conda-forge-converter --batch --pattern '*ml*'")
        print("\nExample 3: Convert everything except test environments")
        print("  conda-forge-converter --batch --exclude 'test_*'")
        print("\nExample 4: Convert environments with advanced logging and parallelism")
        print(
            "  conda-forge-converter --batch --verbose --max-parallel 4 --log-file conversion.log"
        )
        print("\nExample 5: Full workflow with health checks, verification and reporting")
        print(
            "  conda-forge-converter -s myenv -t myenv_forge --health-check --verify --generate-report report.json"
        )


def main(args: Sequence[str] | None = None) -> int:
    """Main entry point for the conda-forge-converter command-line interface.

    This function orchestrates the entire process of converting Anaconda environments to
    conda-forge environments. It handles the following operations:

    1. Parsing command-line arguments
    2. Setting up logging based on verbosity settings
    3. Processing special commands (help, health, report, update)
    4. Executing environment conversions (single or batch mode)
    5. Generating reports and performing health checks as requested

    The function supports different modes of operation:
    - Help mode: Shows detailed help information on specific topics
    - Health check mode: Analyzes an environment's health
    - Report mode: Generates detailed conversion reports
    - Update mode: Updates or analyzes drift in existing conda-forge environments
    - Single environment conversion: Converts a single named environment
    - Batch conversion: Converts multiple environments matching criteria

    Args:
    ----
        args: Command-line arguments to parse. If None, sys.argv[1:] is used.
            These arguments control all aspects of the converter's behavior.

    Returns:
    -------
        Exit code:
        - 0 for success
        - 1 for failure (errors during conversion, invalid arguments, etc.)

    Raises:
    ------
        No exceptions are raised directly; all errors are logged and reflected in
        the return code.

    Examples:
    --------
        # Direct invocation with arguments
        >>> exit_code = main(["--source-env", "myenv", "--target-env", "myenv_forge"])

        # Process arguments from command line
        >>> exit_code = main()  # Uses sys.argv[1:]

    """
    parsed_args = parse_args(args)

    # Setup logging with global logger
    setup_logging(parsed_args.log_file, parsed_args.verbose)

    # Handle special commands
    if parsed_args.command == "help":
        show_help(parsed_args.topic)
        return 0

    # Handle health check command
    if parsed_args.command == "health":
        env_name = parsed_args.environment

        # Run health check
        health_result = check_environment_health(env_name, parsed_args.verbose)

        # Verify environment if requested
        if parsed_args.verify:
            verify_result = verify_environment(env_name, verbose=parsed_args.verbose)
            health_result["verification"] = {
                "success": verify_result,
                "timestamp": datetime.now().isoformat(),
            }

        # Save results to file if requested
        if parsed_args.output:
            try:
                with open(parsed_args.output, "w") as f:
                    json.dump(health_result, f, indent=2)
                logger.info(f"Health check results saved to {parsed_args.output}")
            except Exception as e:
                logger.error(f"Failed to save health check results: {str(e)}")

        # Return success or failure
        return 0 if health_result["status"] != "ERROR" else 1

    # Handle report command
    if parsed_args.command == "report":
        # Generate report for existing environments
        report = generate_conversion_report(
            parsed_args.source,
            parsed_args.target,
            True,  # Assume success since both environments exist
            output_file=parsed_args.output,
            verbose=parsed_args.verbose,
        )

        # Print summary if requested
        if parsed_args.print:
            print_report_summary(report)

        return 0

    # Handle update command
    if parsed_args.command == "update":
        env_name = parsed_args.environment

        # Just detect drift if requested
        if parsed_args.drift:
            drift_result = detect_drift(env_name, parsed_args.verbose)

            # Print summary of drift
            source_env = (
                env_name.replace("_forge", "")
                if env_name.endswith("_forge")
                else f"{env_name}_source"
            )
            print(f"\n=== Environment Drift: {source_env} → {env_name} ===")

            if "error" in drift_result:
                print(f"Error: {drift_result['error']}")
                return 1

            print(f"Source packages: {drift_result.get('source_package_count', 0)}")
            print(f"Target packages: {drift_result.get('target_package_count', 0)}")
            print(f"Same versions: {len(drift_result.get('same_versions', []))}")
            print(f"Different versions: {len(drift_result.get('different_versions', []))}")
            print(f"Only in source: {len(drift_result.get('source_only', []))}")
            print(f"Only in target: {len(drift_result.get('target_only', []))}")

            if "environment_similarity" in drift_result:
                print(f"Environment similarity: {drift_result['environment_similarity']}%")

            return 0

        # Otherwise, update the environment
        update_result = update_conda_forge_environment(
            env_name,
            update_all=parsed_args.all,
            add_missing=parsed_args.add_missing,
            specific_packages=parsed_args.packages,
            dry_run=parsed_args.dry_run,
            verbose=parsed_args.verbose,
        )

        # Save report if requested
        if parsed_args.report:
            try:
                with open(parsed_args.report, "w") as f:
                    json.dump(update_result, f, indent=2)
                logger.info(f"Update report saved to {parsed_args.report}")
            except Exception as e:
                logger.error(f"Failed to save update report: {str(e)}")

        # Determine success based on whether any operations failed
        if (
            len(update_result.get("failed_updates", [])) > 0
            or len(update_result.get("failed_additions", [])) > 0
        ):
            return 1
        return 0

    # Regular conversion logic
    if parsed_args.batch:
        # Batch mode - convert multiple environments
        if parsed_args.health_check:
            logger.info("Running health checks on environments before conversion...")
            # Health checks will be performed in convert_multiple_environments

        results = convert_multiple_environments(
            parsed_args.pattern,
            parsed_args.target_suffix,
            parsed_args.dry_run,
            parsed_args.verbose,
            parsed_args.exclude,
            parsed_args.max_parallel,
            not parsed_args.no_backup,
            parsed_args.search_path,
        )

        # Generate summary report if requested
        if parsed_args.generate_report and results:
            # Ensure results is a dictionary before passing to generate_summary_report
            if isinstance(results, dict):
                summary_report = generate_summary_report(results, parsed_args.generate_report)
                logger.info(f"Conversion summary report saved to {parsed_args.generate_report}")

        success = bool(results)
    else:
        # Single environment mode
        if not parsed_args.source_env:
            logger.error("In single environment mode, --source-env is required")
            return 1

        # Get all environments
        environments = list_all_conda_environments(verbose=parsed_args.verbose)

        # Check if source environment exists
        if parsed_args.source_env not in environments:
            # Try checking if it's a path to an environment
            if not is_conda_environment(parsed_args.source_env):
                logger.error(f"Source environment '{parsed_args.source_env}' not found")
                return 1

            logger.info(f"Using environment at path: {parsed_args.source_env}")
            env_path = parsed_args.source_env
        else:
            env_path = environments[parsed_args.source_env]

        # Default target environment name if not specified
        target_env = parsed_args.target_env or f"{parsed_args.source_env}_forge"

        # Run health check on source environment if requested
        if parsed_args.health_check:
            logger.info(f"Running health check on source environment '{parsed_args.source_env}'...")
            health_result = check_environment_health(parsed_args.source_env, parsed_args.verbose)

            # If there are critical issues, abort
            if health_result["status"] == "ERROR":
                logger.error("Health check failed - aborting conversion")
                return 1

            # If there are warnings, let the user know but continue
            if health_result["status"] == "WARNING" and health_result["issues"]:
                logger.warning(
                    "Health check found non-critical issues - continuing with conversion"
                )

        # Do the actual conversion
        success = convert_environment(
            parsed_args.source_env,
            target_env,
            parsed_args.python,
            parsed_args.dry_run,
            parsed_args.verbose,
            env_path,
        )

        if success and not parsed_args.dry_run:
            # Generate report if requested
            if parsed_args.generate_report:
                report = generate_conversion_report(
                    parsed_args.source_env,
                    target_env,
                    success,
                    output_file=parsed_args.generate_report,
                    verbose=parsed_args.verbose,
                )
                logger.info(f"Conversion report saved to {parsed_args.generate_report}")

                # Print summary
                print_report_summary(report)

            # Verify target environment if requested
            if parsed_args.verify:
                logger.info(f"Verifying target environment '{target_env}'...")
                verify_result = verify_environment(target_env, verbose=parsed_args.verbose)

                if not verify_result:
                    logger.error("Target environment verification failed")
                    # Don't consider this a failure for the exit code
                    # since the conversion itself succeeded

            # Health check on target environment if requested
            if parsed_args.health_check:
                logger.info(f"Running health check on target environment '{target_env}'...")
                target_health = check_environment_health(target_env, parsed_args.verbose)

                if target_health["status"] != "GOOD":
                    logger.warning("Target environment health check found issues")
                    # Don't consider this a failure for the exit code

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
