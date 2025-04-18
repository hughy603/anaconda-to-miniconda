"""Logging configuration for GitHub Actions workflow validation."""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create logger
logger = logging.getLogger("github_actions_validator")


def configure_logging(
    level: int | str = DEFAULT_LOG_LEVEL,
    log_file: str | None = None,
    verbose: bool = False,
) -> None:
    """Configure logging for the application.

    Args:
        level: The log level (default: INFO)
        log_file: Path to log file (optional)
        verbose: Enable verbose logging (sets level to DEBUG)
    """
    # Set log level based on verbose flag
    if verbose:
        level = logging.DEBUG

    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Create file handler if log file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configure our logger
    logger.setLevel(level)

    logger.debug("Logging configured with level %s", logging.getLevelName(level))
    if log_file:
        logger.debug("Logging to file: %s", log_file)


class ProcessTimer:
    """Timer for tracking process execution time and detecting hanging processes."""

    def __init__(self, name: str, timeout: int = 300) -> None:
        """Initialize the process timer.

        Args:
            name: Name of the process being timed
            timeout: Timeout in seconds (default: 300)
        """
        self.name: str = name
        self.timeout: int = timeout
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.last_progress_time: float | None = None
        self.progress_updates: list[tuple[float, str]] = []

    def start(self) -> None:
        """Start the timer."""
        current_time: float = time.time()
        self.start_time = current_time
        self.last_progress_time = current_time
        logger.debug("Started process '%s'", self.name)

    def update_progress(self, message: str) -> None:
        """Update progress for the process.

        Args:
            message: Progress message
        """
        now: float = time.time()

        # Ensure start_time is not None
        if self.start_time is None:
            # Initialize start time if not already set
            self.start()
            elapsed: float = 0.0
        else:
            elapsed = now - self.start_time

        # Calculate time since last progress update
        since_last: float = 0.0
        if self.last_progress_time is not None:
            since_last = now - self.last_progress_time

        self.last_progress_time = now
        self.progress_updates.append((now, message))

        logger.debug(
            "Progress update for '%s' after %.2fs (+%.2fs): %s",
            self.name,
            elapsed,
            since_last,
            message,
        )

    def end(self) -> float:
        """End the timer and return the elapsed time.

        Returns:
            Elapsed time in seconds
        """
        now: float = time.time()
        self.end_time = now

        # Ensure start_time is not None
        if self.start_time is None:
            # Initialize start time if not already set
            self.start()
            return 0.0

        elapsed: float = now - self.start_time

        logger.debug("Completed process '%s' in %.2fs", self.name, elapsed)
        return elapsed

    def check_timeout(self) -> bool:
        """Check if the process has timed out.

        Returns:
            True if the process has timed out, False otherwise
        """
        if self.start_time is None:
            return False

        if self.end_time is not None:
            return False

        now: float = time.time()
        elapsed: float = now - self.start_time

        if elapsed > self.timeout:
            logger.warning(
                "Process '%s' timed out after %.2fs (timeout: %ds)",
                self.name,
                elapsed,
                self.timeout,
            )
            return True

        # Log a warning if no progress updates for a while
        if self.last_progress_time is not None:
            time_since_update: float = now - self.last_progress_time
            if time_since_update > self.timeout / 3:
                logger.warning(
                    "No progress updates for '%s' in %.2fs", self.name, time_since_update
                )

        return False

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the process execution.

        Returns:
            Dictionary with process execution summary
        """
        now: float = time.time()

        if self.start_time is None:
            return {"status": "not_started", "name": self.name}

        if self.end_time is None:
            elapsed: float = now - self.start_time
            time_since_last: float | None = None

            if self.last_progress_time is not None:
                time_since_last = now - self.last_progress_time

            return {
                "status": "running",
                "name": self.name,
                "elapsed": elapsed,
                "progress_updates": len(self.progress_updates),
                "last_update": self.last_progress_time,
                "time_since_last_update": time_since_last,
            }

        elapsed = self.end_time - self.start_time
        return {
            "status": "completed",
            "name": self.name,
            "elapsed": elapsed,
            "progress_updates": len(self.progress_updates),
        }


def get_log_file_path() -> str:
    """Get the path to the log file.

    Returns:
        Path to the log file
    """
    log_dir = Path(".github_actions_validator_logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(log_dir / f"validation_{timestamp}.log")
