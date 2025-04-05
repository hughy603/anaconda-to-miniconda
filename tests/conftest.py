"""Pytest configuration for conda-forge-converter tests."""

import os
import pytest
import logging
from unittest import mock

# Ensure we don't mess with real environments during tests
@pytest.fixture(autouse=True)
def disable_real_command_execution():
    """Prevent actual subprocess commands from running during tests."""
    with mock.patch("subprocess.run") as _:
        yield

# Prevent polluting logs during tests
@pytest.fixture(autouse=True)
def disable_logging():
    """Disable logging during tests."""
    with mock.patch("logging.Logger.debug"), \
         mock.patch("logging.Logger.info"), \
         mock.patch("logging.Logger.warning"), \
         mock.patch("logging.Logger.error"), \
         mock.patch("logging.Logger.critical"):
        yield