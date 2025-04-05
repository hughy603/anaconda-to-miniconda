"""Utilities for the conda-forge-converter package.

This module provides utility functions used throughout the conda-forge-converter
package, including logging setup, command execution, and filesystem operations.
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal, TypeAlias, TypeGuard

# Type aliases for improved readability
CommandOutput: TypeAlias = str | bool | None  # Output from run_command
PathLike: TypeAlias = str | Path
LogLevel: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Create a logger
logger = logging.getLogger("conda_converter")


def setup_logging(log_file: str | None = None, verbose: bool = False) -> None:
    """Configure logging to file and console.

    Sets up the global logger with appropriate handlers and formatters. If verbose is True,
    sets logging level to DEBUG, otherwise uses INFO level. If a log_file is provided,
    logs will be written to that file in addition to the console.

    Args:
    ----
        log_file: Optional path to a log file. If provided, logs will be written here.
        verbose: Whether to enable verbose (DEBUG level) logging.

    Examples:
    --------
        >>> setup_logging(verbose=True)  # Setup console logging with debug level
        >>> setup_logging("/tmp/converter.log")  # Log to file with INFO level
        >>> setup_logging("/tmp/converter.log", True)  # Log to file with DEBUG level

    """
    # Set the log level based on verbosity
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Add file handler if log file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


def run_command(
    cmd: list[str], verbose: bool = False, capture: bool = True, timeout: int | None = None
) -> CommandOutput:
    """Run a command and return its output, with optional verbose logging.

    This function is the primary way to execute external commands in the application.
    It handles command execution, output capturing, error handling, and timeouts.

    Args:
    ----
        cmd: List of command components to run (e.g., ["conda", "env", "list"])
        verbose: Whether to log detailed command information and error output
        capture: Whether to capture and return command output as a string
        timeout: Maximum time in seconds to wait for command completion

    Returns:
    -------
        If capture is True and command succeeds: command output as a string
        If capture is False and command succeeds: True
        If command fails: None

    Raises:
    ------
        No exceptions are raised directly, but failure information is logged.

    Examples:
    --------
        >>> # Run a simple command and get output
        >>> output = run_command(["conda", "info"])
        >>> if is_command_output_str(output):
        ...     print(output)

        >>> # Run a command without capturing output (for long-running operations)
        >>> success = run_command(["conda", "env", "create"], capture=False)
        >>> print("Success" if success else "Failed")

        >>> # Run a command with a timeout
        >>> output = run_command(["conda", "env", "list"], timeout=10)

    """
    if verbose:
        logger.debug(f"Running: {' '.join(cmd)}")

    try:
        if capture:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=timeout
            )
            return result.stdout
        # Run without capturing output (for long-running commands)
        subprocess.run(cmd, check=True, timeout=timeout)
        return True
    except subprocess.CalledProcessError as e:
        if verbose or not capture:
            logger.error(f"Command failed with exit code {e.returncode}")
            logger.error(f"Command: {' '.join(cmd)}")
            if e.stdout:
                logger.error("STDOUT:")
                logger.error(e.stdout)
            if e.stderr:
                logger.error("STDERR:")
                logger.error(e.stderr)
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running command: {e}")
        logger.error(f"Command was: {' '.join(cmd)}")
        return None


def is_command_output_str(output: CommandOutput) -> TypeGuard[str]:
    """Type guard to check if command output is a string.

    This is a type guard function that helps with type checking when working with
    the output of the run_command function. It allows static type checkers to know
    that the output is a string when this function returns True.

    Args:
    ----
        output: The output from run_command to check.

    Returns:
    -------
        True if output is a string, False otherwise.

    Examples:
    --------
        >>> output = run_command(["conda", "env", "list"])
        >>> if is_command_output_str(output):
        ...     # Type checkers know output is str here
        ...     lines = output.splitlines()
        >>> else:
        ...     # Handle the case where the command failed
        ...     print("Command failed")

    """
    return isinstance(output, str)


def check_disk_space(needed_gb: float = 5, path: PathLike | None = None) -> bool:
    """Check if there's enough disk space available.

    Verifies that the specified path (or current directory if not specified)
    has at least the requested amount of free disk space.

    Args:
    ----
        needed_gb: Required gigabytes of free space.
        path: Path to check, defaults to current directory.

    Returns:
    -------
        True if enough space is available, False otherwise.

    Examples:
    --------
        >>> # Check if current directory has at least 10GB free
        >>> if check_disk_space(10):
        ...     print("Enough space available")
        >>> else:
        ...     print("Not enough space")

        >>> # Check if specific directory has at least 5GB free
        >>> check_disk_space(5, "/path/to/check")

    """
    if path is None:
        path_obj = Path.cwd()
    else:
        path_obj = Path(path)

    try:
        _total, _used, free = shutil.disk_usage(path_obj)
        free_gb = free / (1024**3)  # Convert to GB

        if free_gb < needed_gb:
            logger.warning(
                f"Only {free_gb:.1f} GB free space available. Recommended minimum: {needed_gb} GB",
            )
            return False
        return True
    except OSError as e:
        logger.error(f"Error checking disk space at {path_obj}: {str(e)}")
        return False


def is_conda_environment(path: PathLike) -> bool:
    """Check if a directory is a conda environment.

    Determines if the specified path appears to be a conda environment by
    checking for typical conda environment directory structures.

    Args:
    ----
        path: Path to the directory to check.

    Returns:
    -------
        True if the directory appears to be a conda environment.

    Examples:
    --------
        >>> # Check if a directory is a conda environment
        >>> if is_conda_environment("/path/to/myenv"):
        ...     print("This is a conda environment")
        >>> else:
        ...     print("This is not a conda environment")

    """
    path_obj = Path(path)

    # A conda environment typically has these subdirectories
    conda_meta = path_obj / "conda-meta"

    # Different paths based on OS
    is_windows = sys.platform.startswith("win")
    if is_windows:
        bin_dir = path_obj / "Scripts"
        python_exec = path_obj / "python.exe"
    else:
        bin_dir = path_obj / "bin"
        python_exec = bin_dir / "python"

    # If conda-meta exists and either python or bin/Scripts exists, it's likely a conda env
    return conda_meta.exists() and (python_exec.exists() or bin_dir.exists())


def set_log_level(level: LogLevel) -> None:
    """Set the logger's level based on a string identifier.

    Changes the logging level of the global logger to the specified level.

    Args:
    ----
        level: The log level to set ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").

    Examples:
    --------
        >>> set_log_level("DEBUG")  # Set to debug level
        >>> set_log_level("WARNING")  # Set to warning level

    """
    if level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif level == "INFO":
        logger.setLevel(logging.INFO)
    elif level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif level == "ERROR":
        logger.setLevel(logging.ERROR)
    elif level == "CRITICAL":
        logger.setLevel(logging.CRITICAL)
    else:
        logger.warning(f"Unknown log level: {level}")
