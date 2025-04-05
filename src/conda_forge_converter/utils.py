"""Utilities for the conda-forge-converter package."""

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

    Args:
    ----
        log_file: Optional path to a log file. If provided, logs will be written here.
        verbose: Whether to enable verbose (DEBUG level) logging.

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


def run_command(cmd: list[str], verbose: bool = False, capture: bool = True) -> CommandOutput:
    """Run a command and return its output, with optional verbose logging.

    Args:
    ----
        cmd: List of command components to run.
        verbose: Whether to log detailed command information.
        capture: Whether to capture and return command output.

    Returns:
    -------
        If capture is True, returns the command output as a string on success.
        If capture is False but command succeeds, returns True.
        Returns None if the command fails.

    """
    if verbose:
        logger.debug(f"Running: {' '.join(cmd)}")

    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        # Run without capturing output (for long-running commands)
        subprocess.run(cmd, check=True)
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


def is_command_output_str(output: CommandOutput) -> TypeGuard[str]:
    """Type guard to check if command output is a string.

    Args:
    ----
        output: The output from run_command to check.

    Returns:
    -------
        True if output is a string, False otherwise.

    """
    return isinstance(output, str)


def check_disk_space(needed_gb: float = 5, path: PathLike | None = None) -> bool:
    """Check if there's enough disk space available.

    Args:
    ----
        needed_gb: Required gigabytes of free space.
        path: Path to check, defaults to current directory.

    Returns:
    -------
        True if enough space is available, False otherwise.

    """
    if path is None:
        path_obj = Path.cwd()
    else:
        path_obj = Path(path)

    _total, _used, free = shutil.disk_usage(path_obj)
    free_gb = free / (1024**3)  # Convert to GB

    if free_gb < needed_gb:
        logger.warning(
            f"Only {free_gb:.1f} GB free space available. Recommended minimum: {needed_gb} GB",
        )
        return False
    return True


def is_conda_environment(path: PathLike) -> bool:
    """Check if a directory is a conda environment.

    Args:
    ----
        path: Path to the directory to check.

    Returns:
    -------
        True if the directory appears to be a conda environment.

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

    Args:
    ----
        level: The log level to set.

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
