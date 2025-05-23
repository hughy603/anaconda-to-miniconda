"""Conda-Forge Converter.

A utility package for converting Anaconda environments to conda-forge environments
while preserving the top-level dependency versions. This package helps in the migration
from Anaconda to the community-maintained conda-forge channel.

Key features:
- Convert single or multiple conda environments
- Preserve exact package versions during conversion
- Discover environments in custom paths
- Support for both conda and pip packages within environments
- Parallel processing for batch conversions
"""

from conda_forge_converter._version import __version__

from .cli import main
from .core import (
    EnvironmentInfo,
    convert_environment,
    convert_multiple_environments,
    environment_exists,
    get_environment_packages,
    list_all_conda_environments,
)
from .health import check_environment_health, verify_environment
from .incremental import detect_drift, update_conda_forge_environment
from .reporting import (
    generate_conversion_report,
    generate_summary_report,
    print_report_summary,
)
from .utils import setup_logging

__all__ = [
    "EnvironmentInfo",
    "__version__",
    "check_environment_health",
    "convert_environment",
    "convert_multiple_environments",
    "detect_drift",
    "environment_exists",
    "generate_conversion_report",
    "generate_summary_report",
    "get_environment_packages",
    "list_all_conda_environments",
    "main",
    "print_report_summary",
    "setup_logging",
    "update_conda_forge_environment",
    "verify_environment",
]
