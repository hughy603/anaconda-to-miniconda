"""Progress visualization for long-running operations."""

import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, TypeAlias, TypeVar

from .utils import logger

T = TypeVar("T")
R = TypeVar("R")
ProgressCallback: TypeAlias = Callable[[int, int, float], None]


@dataclass
class ProgressBar:
    """Progress bar for tracking operation progress."""

    total: int
    prefix: str = ""
    suffix: str = ""
    decimals: int = 1
    length: int = 50
    fill: str = "█"
    print_end: str = "\r"
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    update_interval: float = 0.1  # seconds between updates
    current: int = 0
    _last_percent: int = 0

    def update(self, n: int = 1) -> None:
        """Update the progress bar.

        Args:
            n: Number of steps to increment

        """
        self.current += n
        current_time = time.time()

        # Only update display if enough time has passed
        if current_time - self.last_update < self.update_interval:
            return

        self.last_update = current_time

        # Calculate percentage
        percent = int(100 * (self.current / float(self.total)))

        # Only update if percentage has changed
        if percent == self._last_percent:
            return

        self._last_percent = percent

        # Calculate filled length
        filled_length = int(self.length * self.current // self.total)

        # Create the bar
        bar = self.fill * filled_length + "-" * (self.length - filled_length)

        # Calculate elapsed time
        elapsed_time = current_time - self.start_time

        # Estimate remaining time
        if self.current > 0:
            estimated_total = elapsed_time * (self.total / self.current)
            remaining_time = estimated_total - elapsed_time
            eta_str = self._format_time(remaining_time)
        else:
            eta_str = "unknown"

        # Format elapsed time
        elapsed_str = self._format_time(elapsed_time)

        # Create the progress string
        progress_str = (
            f"\r{self.prefix} |{bar}| {percent}% "
            f"[{self.current}/{self.total}] "
            f"Elapsed: {elapsed_str} ETA: {eta_str} {self.suffix}"
        )

        # Print the progress bar
        sys.stdout.write(progress_str)
        sys.stdout.flush()

        # Print new line if complete
        if self.current == self.total:
            print()

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to a human-readable string.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string

        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        if seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        hours = seconds / 3600
        return f"{hours:.1f}h"


class ProgressTracker:
    """Track progress of a long-running operation."""

    def __init__(
        self,
        total: int,
        description: str = "Processing",
        unit: str = "items",
    ) -> None:
        """Initialize the progress tracker.

        Args:
            total: Total number of items to process
            description: Description of the progress
            unit: Unit of progress (e.g., "items", "files", etc.)

        """
        self.total = total
        self.description = description
        self.unit = unit
        self.current = 0
        self.start_time = time.time()
        self.last_update = 0
        self._display_interval = 0.1  # seconds between updates

    def update(self, n: int = 1) -> None:
        """Update the progress.

        Args:
            n: Number of items processed since last update

        """
        self.current += n
        current_time = time.time()

        # Only update display if enough time has passed
        if current_time - self.last_update >= self._display_interval:
            self._display_progress()
            self.last_update = current_time

    def _display_progress(self) -> None:
        """Display the current progress."""
        elapsed = time.time() - self.start_time
        if self.current > 0:
            rate = self.current / elapsed
            eta = (self.total - self.current) / rate if rate > 0 else 0
        else:
            rate = 0
            eta = 0

        percent = (self.current / self.total) * 100 if self.total > 0 else 0

        # Format progress message
        message = (
            f"{self.description}: {self.current}/{self.total} {self.unit} "
            f"({percent:.1f}%) - {rate:.1f} {self.unit}/s - ETA: {eta:.1f}s"
        )

        # Clear previous line and print new progress
        print("\r" + " " * 80 + "\r" + message, end="", flush=True)

    def complete(self) -> dict[str, Any]:
        """Return completion status."""
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        return {
            "description": self.description,
            "total": self.total,
            "completed": self.current,
            "elapsed_time": elapsed,
            "rate": rate,
        }

    def __enter__(self) -> "ProgressTracker":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.finish()

    def finish(self) -> None:
        """Finish progress tracking."""
        if self.current < self.total:
            self.update(self.total - self.current)


class MultiProgressTracker:
    """Tracker for monitoring multiple operations."""

    def __init__(
        self,
        operations: dict[str, int],
        show_progress: bool = True,
        log_level: str = "info",
    ) -> None:
        """Initialize the multi-progress tracker.

        Args:
            operations: Dictionary mapping operation names to total steps
            show_progress: Whether to show progress bars
            log_level: Log level for progress updates

        """
        self.operations = operations
        self.show_progress = show_progress
        self.log_level = log_level
        self.trackers: dict[str, ProgressTracker] = {}
        for name, total in operations.items():
            self.trackers[name] = ProgressTracker(
                total=total,
                description=name,
                unit="items",
            )

    def update(self, operation: str, n: int = 1, item_info: dict[str, Any] | None = None) -> None:
        """Update progress for a specific operation.

        Args:
            operation: Name of the operation to update
            n: Number of steps to increment
            item_info: Information about the completed items

        """
        if operation in self.trackers:
            self.trackers[operation].update(n)
        else:
            logger.warning(f"Unknown operation: {operation}")

    def complete(self, operation: str | None = None) -> dict[str, Any]:
        """Mark all operations as complete.

        This method should be called when all operations are finished.

        Args:
            operation: Name of the operation to complete, or None for all

        Returns:
            Summary of the operation(s)

        """
        if operation:
            if operation in self.trackers:
                self.trackers[operation].update(
                    self.operations[operation] - self.trackers[operation].current
                )
                return {operation: self.trackers[operation].complete()}
            logger.warning(f"Unknown operation: {operation}")
            return {}
        # Complete all operations
        summaries = {}
        for name, tracker in self.trackers.items():
            summaries[name] = tracker.complete()
        return summaries


def with_progress(
    total: int,
    description: str = "Operation",
    show_progress: bool = True,
    log_level: str = "info",
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Decorator to add progress tracking to a function."""

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        def wrapper(*args: Any, **kwargs: Any) -> R:
            tracker = ProgressTracker(
                total=total,
                description=description,
                unit="items",
            )
            try:
                return func(*args, **kwargs)
            finally:
                tracker.finish()

        return wrapper

    return decorator


def track_progress(
    total: int,
    description: str = "Processing",
    unit: str = "items",
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Decorator to track progress of a function.

    Args:
        total: Total number of items to process
        description: Description of the progress
        unit: Unit of progress (e.g., "items", "files", etc.)

    Returns:
        Decorated function that tracks progress

    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        def wrapper(*args: Any, **kwargs: Any) -> R:
            tracker = ProgressTracker(
                total=total,
                description=description,
                unit=unit,
            )
            try:
                result = func(*args, **kwargs)
                tracker.update(total)
                return result
            finally:
                tracker.finish()

        return wrapper

    return decorator


def track_progress_with_callback(
    total: int,
    description: str = "Operation",
    callback: ProgressCallback | None = None,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Decorator to add progress tracking with callback to a function."""

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        def wrapper(*args: Any, **kwargs: Any) -> R:
            tracker = ProgressTracker(
                total=total,
                description=description,
            )
            try:
                result = func(*args, **kwargs)
                tracker.finish()
                if callback:
                    status = tracker.complete()
                    callback(
                        status["completed"],
                        status["total"],
                        status["rate"],
                    )
                return result
            except Exception:
                tracker.finish()
                raise

        return wrapper

    return decorator
