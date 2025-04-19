"""Entry point module for the conda-forge-converter package.

This module allows the package to be run as a script using
`python -m conda_forge_converter`.
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
