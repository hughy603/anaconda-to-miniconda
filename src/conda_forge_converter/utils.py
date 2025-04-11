"""Utilities for the conda-forge-converter package.

This module provides utility functions used throughout the conda-forge-converter
package, including logging setup, command execution, filesystem operations, and
user/permission management.

The module is organized into the following functional categories:

Logging Functions:
  - setup_logging: Configure logging to file and console
  - set_log_level: Set the logger's level based on a string identifier

Command Execution:
  - run_command: Run a command and return its output
  - is_command_output_str: Type guard to check if command output is a string

Filesystem Operations:
  - check_disk_space: Check if there's enough disk space available
  - is_conda_environment: Check if a directory is a conda environment

User and Permissions:
  - is_root: Check if the current process is running as root
  - get_path_owner: Get the user and group IDs of a file or directory
  - get_owner_names: Get the user and group names from their IDs
  - change_path_owner: Change the owner of a file or directory

Type Aliases:
  - CommandOutput: Output type from run_command (str | bool | None)
  - PathLike: Path-like object (str | Path)
  - LogLevel: Valid logging levels ("DEBUG", "INFO", etc.)

Global Variables:
  - logger: The global logger for the conda-forge-converter package
"""

import logging
import os
import sys

# Import Unix-specific modules only on Unix-like systems
try:
    import grp
    import pwd as user_module  # Renamed to avoid gitleaks false positive
except ImportError:
    grp = None  # Not available on Windows
    user_module = None  # Not available on Windows
import shutil
import subprocess
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
        logger.error(f"Error checking disk space at {path_obj}: {e!s}")
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


def is_root() -> bool:
    """Check if the current process is running as root.

    This function is particularly useful when running operations that may
    require elevated privileges, such as changing file ownership or
    installing packages system-wide. The converter uses this to determine
    whether to apply special handling for root-executed operations.

    Returns:
    -------
        True if running as root (UID 0), False otherwise.
        On Windows, always returns False.

    Examples:
    --------
        >>> if is_root():
        ...     print("Running as root - will preserve ownership")
        ... else:
        ...     print("Not running as root")
    """
    if sys.platform.startswith("win"):
        # On Windows, return False (no direct equivalent of root)
        return False
    else:
        # On Unix-like systems, check if UID is 0
        try:
            # Type ignore for pyright - geteuid is Unix-specific
            return os.geteuid() == 0  # type: ignore
        except AttributeError:
            # If geteuid is not available for some reason
            return False


def get_path_owner(path: PathLike) -> tuple[int, int]:
    """Get the user and group IDs of a file or directory.

    This function retrieves the numeric user ID (UID) and group ID (GID)
    that own a specified file or directory. This is useful when preserving
    ownership during operations like environment conversion.

    Args:
    ----
        path: Path to the file or directory as a string or Path object

    Returns:
    -------
        Tuple of (uid, gid) containing the numeric user and group IDs

    Examples:
    --------
        >>> uid, gid = get_path_owner("/path/to/file")
        >>> print(f"File is owned by UID {uid} and GID {gid}")

        >>> # Get owner of a directory using a Path object
        >>> from pathlib import Path
        >>> uid, gid = get_path_owner(Path("/path/to/directory"))

    Raises:
    ------
        FileNotFoundError: If the specified path does not exist
        PermissionError: If the current user doesn't have permission to access the path
    """
    path_obj = Path(path)
    stat_info = path_obj.stat()
    return (stat_info.st_uid, stat_info.st_gid)


def get_owner_names(uid: int, gid: int) -> tuple[str, str]:
    """Get the user and group names from their numeric IDs.

    This function converts numeric user ID (UID) and group ID (GID) values
    to their corresponding username and group name. This is useful for
    displaying human-readable ownership information.

    Args:
    ----
        uid: User ID (numeric)
        gid: Group ID (numeric)

    Returns:
    -------
        Tuple of (username, groupname) as strings
        If the UID or GID cannot be resolved to a name, "unknown" is returned
        for the corresponding value
        On Windows, returns ("unknown", "unknown")

    Examples:
    --------
        >>> username, groupname = get_owner_names(1000, 1000)
        >>> print(f"Owner: {username}, Group: {groupname}")

        >>> # Handle case where user/group might not exist
        >>> username, groupname = get_owner_names(9999, 9999)
        >>> if username == "unknown":
        ...     print("User ID not found in system")
    """
    # On Windows, these modules aren't available
    if sys.platform.startswith("win") or user_module is None or grp is None:
        return ("unknown", "unknown")

    try:
        # Type ignore for pyright - getpwuid and getgrgid are Unix-specific
        username = user_module.getpwuid(uid).pw_name  # type: ignore
        groupname = grp.getgrgid(gid).gr_name  # type: ignore
        return (username, groupname)
    except KeyError:
        logger.warning(f"Could not find user/group for UID={uid}, GID={gid}")
        return ("unknown", "unknown")


def change_path_owner(path: PathLike, uid: int, gid: int, recursive: bool = True) -> bool:
    """Change the owner of a file or directory.

    This function changes the ownership of a file or directory to the specified
    user ID (UID) and group ID (GID). When recursive=True (the default), it will
    change ownership of all files and subdirectories within a directory.

    This is particularly useful when running as root and needing to preserve
    the original ownership of files after operations like environment conversion.

    Args:
    ----
        path: Path to the file or directory as a string or Path object
        uid: User ID to set as owner (numeric)
        gid: Group ID to set as group (numeric)
        recursive: Whether to change ownership recursively for directories (default: True)

    Returns:
    -------
        True if ownership change was successful, False otherwise
        On Windows, always returns True (ownership change is not supported)

    Examples:
    --------
        >>> # Change ownership of a file
        >>> success = change_path_owner("/path/to/file", 1000, 1000, recursive=False)
        >>> if success:
        ...     print("Ownership changed successfully")

        >>> # Change ownership of a directory and all its contents
        >>> change_path_owner("/path/to/directory", 1000, 1000)

        >>> # Get current owner and change ownership
        >>> uid, gid = get_path_owner("/path/to/file")
        >>> change_path_owner("/path/to/new_file", uid, gid)
    """
    # On Windows, ownership change is not supported in the same way
    if sys.platform.startswith("win"):
        logger.debug("Ownership change not supported on Windows, skipping")
        return True

    path_obj = Path(path)

    try:
        if not recursive or path_obj.is_file():
            # Type ignore for pyright - chown is Unix-specific
            os.chown(path_obj, uid, gid)  # type: ignore
        else:
            # Recursively change ownership of all files and directories
            for root, _dirs, files in os.walk(path_obj):
                root_path = Path(root)
                os.chown(root_path, uid, gid)  # type: ignore
                for file in files:
                    file_path = root_path / file
                    os.chown(file_path, uid, gid)  # type: ignore
        return True
    except (PermissionError, OSError) as e:
        logger.error(f"Failed to change ownership of {path}: {e!s}")
        return False
