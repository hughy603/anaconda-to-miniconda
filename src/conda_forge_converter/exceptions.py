"""Custom exceptions for the conda-forge-converter package."""

from typing import Any


class CondaForgeConverterError(Exception):
    """Base exception for all conda-forge-converter errors."""


class CondaEnvironmentError(CondaForgeConverterError):
    """Base exception for environment-related errors."""


class EnvironmentNotFoundError(CondaEnvironmentError):
    """Exception raised when an environment is not found."""

    def __init__(self, env_name: str) -> None:
        """Initialize the exception.

        Args:
            env_name: Name of the environment that was not found

        """
        self.env_name = env_name
        super().__init__(f"Environment '{env_name}' not found")


class EnvironmentCreationError(CondaEnvironmentError):
    """Exception raised when an environment cannot be created."""

    def __init__(self, env_name: str, reason: str) -> None:
        """Initialize the exception.

        Args:
            env_name: Name of the environment that could not be created
            reason: Reason for the failure

        """
        self.env_name = env_name
        self.reason = reason
        super().__init__(f"Failed to create environment '{env_name}': {reason}")


class EnvironmentExportError(CondaEnvironmentError):
    """Exception raised when environment export fails."""


class EnvironmentImportError(CondaEnvironmentError):
    """Exception raised when environment import fails."""


class EnvironmentRemovalError(CondaEnvironmentError):
    """Exception raised when environment removal fails."""


class PackageInstallationError(CondaEnvironmentError):
    """Exception raised when a package cannot be installed."""

    def __init__(self, package_name: str, reason: str) -> None:
        """Initialize the exception.

        Args:
            package_name: Name of the package that could not be installed
            reason: Reason for the failure

        """
        self.package_name = package_name
        self.reason = reason
        super().__init__(f"Failed to install package '{package_name}': {reason}")


class ValidationError(CondaForgeConverterError):
    """Exception raised when validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details

        """
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(CondaForgeConverterError):
    """Exception raised when there is a configuration error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details

        """
        self.details = details or {}
        super().__init__(message)


class DiskSpaceError(CondaForgeConverterError):
    """Base exception for disk space related errors."""

    def __init__(self, required_bytes: int, available_bytes: int) -> None:
        """Initialize the disk space error.

        Args:
            required_bytes: Required disk space in bytes
            available_bytes: Available disk space in bytes

        """
        self.required_bytes = required_bytes
        self.available_bytes = available_bytes
        super().__init__(
            f"Not enough disk space. Required: {self._format_bytes(required_bytes)}, "
            f"Available: {self._format_bytes(available_bytes)}"
        )

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes value to human readable string.

        Args:
            bytes_value: Value in bytes to format

        Returns:
            Formatted string with appropriate unit (B, KB, MB, GB)

        """
        value = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB"]:
            if value < 1024:
                return f"{value:.2f} {unit}"
            value /= 1024
        return f"{value:.2f} TB"


class ConversionError(CondaForgeConverterError):
    """Base exception for environment conversion errors."""

    def __init__(self, source_env: str, target_env: str, message: str) -> None:
        """Initialize the conversion error.

        Args:
            source_env: Name of the source environment
            target_env: Name of the target environment
            message: Error message

        """
        self.source_env = source_env
        self.target_env = target_env
        super().__init__(
            f"Failed to convert environment '{source_env}' to '{target_env}': {message}"
        )
