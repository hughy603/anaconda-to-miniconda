"""Syntax validation for GitHub Actions workflows."""

import re
import subprocess
from pathlib import Path

from ..error_handling import ErrorReporter, ErrorSeverity, ValidationError
from ..logging import ProcessTimer, logger


def validate_syntax(
    workflow_file: Path, error_reporter: ErrorReporter
) -> tuple[bool, list[ValidationError]]:
    """Validate workflow syntax using actionlint.

    Args:
        workflow_file: The workflow file to validate
        error_reporter: The error reporter for formatting errors

    Returns:
        A tuple of (success, errors) where success is a boolean indicating whether
        the workflow syntax is valid, and errors is a list of ValidationError objects
        if any errors were found.
    """
    # Create a process timer for syntax validation
    syntax_timer = ProcessTimer(f"syntax_validation:{workflow_file.name}", timeout=60)
    syntax_timer.start()

    logger.info("Starting syntax validation for workflow: %s", workflow_file)

    errors = []
    try:
        # Run actionlint with timeout
        syntax_timer.update_progress("Running actionlint")
        logger.debug("Running actionlint on workflow: %s", workflow_file)

        cmd = ["pre-commit", "run", "actionlint", "--files", str(workflow_file)]
        logger.debug("Command: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,  # 60 second timeout for syntax validation
        )

        syntax_timer.update_progress(f"actionlint completed with exit code {result.returncode}")

        # Log output for debugging
        if result.stdout:
            logger.debug("actionlint stdout:\n%s", result.stdout)
        if result.stderr:
            logger.debug("actionlint stderr:\n%s", result.stderr)

        if result.returncode != 0:
            syntax_timer.update_progress("Parsing actionlint errors")
            logger.warning("actionlint found issues in workflow: %s", workflow_file)

            # Parse actionlint output for detailed error information
            for line in result.stderr.splitlines() + result.stdout.splitlines():
                if line.strip() and ("error" in line.lower() or "warning" in line.lower()):
                    # Try to extract line number from error message
                    line_number = None
                    line_match = re.search(r":(\d+):", line)
                    if line_match:
                        try:
                            line_number = int(line_match.group(1))
                        except ValueError:
                            pass

                    logger.debug("Found issue at line %s: %s", line_number, line.strip())

                    error = error_reporter.format_error(
                        error_message=line, workflow_name=workflow_file, line_number=line_number
                    )
                    errors.append(error)

            # If no specific errors were found but the command failed, add a generic error
            if not errors:
                logger.warning("actionlint failed but no specific errors were found")
                errors.append(
                    ValidationError(
                        message="Syntax validation failed",
                        severity=ErrorSeverity.ERROR,
                        workflow_file=str(workflow_file),
                        suggestion="Run 'actionlint' manually to see detailed errors.",
                    )
                )
        else:
            logger.info("Syntax validation passed for workflow: %s", workflow_file)

        syntax_timer.update_progress("Syntax validation completed")
        syntax_timer.end()

        return len(errors) == 0, errors

    except subprocess.TimeoutExpired:
        # Handle timeout
        syntax_timer.update_progress("Syntax validation timed out")
        syntax_timer.end()

        logger.error("Syntax validation timed out for workflow: %s", workflow_file)

        errors.append(
            ValidationError(
                message="Syntax validation timed out after 60 seconds",
                severity=ErrorSeverity.ERROR,
                workflow_file=str(workflow_file),
                suggestion="The workflow file may be too complex or there might be an issue "
                "with actionlint.",
            )
        )
        return False, errors

    except FileNotFoundError:
        # actionlint or pre-commit not found
        syntax_timer.update_progress("actionlint or pre-commit not found")
        syntax_timer.end()

        logger.error("actionlint or pre-commit not found")

        errors.append(
            ValidationError(
                message="actionlint or pre-commit not found",
                severity=ErrorSeverity.ERROR,
                workflow_file=str(workflow_file),
                suggestion="Make sure actionlint and pre-commit are installed.",
            )
        )
        return False, errors

    except Exception as e:
        # Handle any other exceptions
        syntax_timer.update_progress(f"Error: {e!s}")
        syntax_timer.end()

        logger.error(
            "Error validating syntax for workflow %s: %s", workflow_file, str(e), exc_info=True
        )

        errors.append(
            ValidationError(
                message=f"Error validating syntax: {e!s}",
                severity=ErrorSeverity.ERROR,
                workflow_file=str(workflow_file),
            )
        )
        return False, errors


def check_actionlint_installed() -> bool:
    """Check if actionlint is installed.

    Returns:
        True if actionlint is installed, False otherwise
    """
    logger.debug("Checking if actionlint is installed")

    try:
        result = subprocess.run(
            ["pre-commit", "run", "actionlint", "--all-files", "--help"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,  # 10 second timeout
        )

        is_installed = "actionlint" in result.stdout or "actionlint" in result.stderr

        if is_installed:
            logger.debug("actionlint is installed")
        else:
            logger.warning("actionlint is not properly configured in pre-commit")

        return is_installed

    except subprocess.TimeoutExpired:
        logger.warning("Timeout while checking for actionlint")
        return False

    except FileNotFoundError:
        logger.warning("pre-commit not found")
        return False

    except Exception as e:
        logger.warning("Error checking for actionlint: %s", str(e))
        return False
