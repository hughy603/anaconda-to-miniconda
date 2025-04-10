"""Version information for conda-forge-converter.

This file is managed by python-semantic-release.
Do not edit manually.
"""

__all__ = ["__version__", "__version_tuple__"]

__version__ = "1.0.0-alpha.1"


# Parse version into tuple for easy access
def _parse_version(version_str: str) -> tuple:
    """Parse version string into a tuple."""
    # Handle pre-release versions (e.g., 1.0.0-alpha.1)
    if "-" in version_str:
        main_version, prerelease = version_str.split("-", 1)
        version_parts = main_version.split(".")
        return (*tuple(int(x) for x in version_parts), prerelease)
    # Handle regular versions (e.g., 1.0.0)
    else:
        version_parts = version_str.split(".")
        return tuple(int(x) for x in version_parts)


__version_tuple__ = _parse_version(__version__)
