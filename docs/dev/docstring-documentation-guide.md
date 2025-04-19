# Docstring-Driven Documentation Guide

This guide explains how to write docstrings for the Conda-Forge Converter project that will be automatically rendered into API documentation.

## Overview

The Conda-Forge Converter uses a docstring-driven documentation approach, where API documentation is generated directly from the docstrings in the source code. This ensures that the documentation is always up-to-date with the code and reduces the maintenance burden.

We use the [mkdocstrings](https://mkdocstrings.github.io/) plugin for MkDocs to extract and render docstrings into the documentation site. The docstrings follow the [Google style format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

## Docstring Structure

### Module Docstrings

Module docstrings should provide an overview of the module's purpose and functionality. They should also include information about the organization of the module, such as the categories of functions or classes it contains.

Example:

```python
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
```

### Function Docstrings

Function docstrings should include:

1. A brief description of what the function does
1. A more detailed description if necessary
1. Parameters (Args)
1. Return values (Returns)
1. Exceptions raised (Raises)
1. Examples
1. Notes or warnings if applicable

Example:

```python
def run_command(
    cmd: list[str],
    verbose: bool = False,
    capture: bool = True,
    timeout: int | None = None,
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
```

### Class Docstrings

Class docstrings should include:

1. A brief description of what the class represents
1. A more detailed description if necessary
1. Attributes
1. Examples of class instantiation and usage

Example:

```python
class EnvironmentConverter:
    """Converts Anaconda environments to conda-forge environments.

    This class handles the conversion of Anaconda environments to conda-forge
    environments. It provides methods for analyzing environments, resolving
    packages, and creating new environments.

    Attributes:
    ----------
        source_env: Name of the source Anaconda environment
        target_env: Name of the target conda-forge environment
        python_version: Python version to use in the target environment
        verbose: Whether to enable verbose logging

    Examples:
    --------
        >>> # Create a converter
        >>> converter = EnvironmentConverter(source_env="myenv", target_env="myenv_forge")
        >>>
        >>> # Convert the environment
        >>> converter.convert()
    """
```

## Documentation Rendering

The docstrings are rendered into the documentation site using the mkdocstrings plugin. Each module has its own documentation page that uses the mkdocstrings directive to render the docstrings.

Example (docs/api/utils.md):

```markdown
# Utils Module

The Utils module provides utility functions used throughout the conda-forge-converter package.

## Overview

This module contains various utility functions that are used by other modules in the package. These functions handle common tasks such as running shell commands, checking disk space, setting up logging, and managing file ownership.

::: conda_forge_converter.utils
    options:
      show_source: true
      show_root_heading: true
      show_category_heading: true
      members_order: source
```

## Best Practices

1. **Keep docstrings up-to-date**: When you modify code, make sure to update the docstrings to reflect the changes.
1. **Include examples**: Examples help users understand how to use the code.
1. **Be specific about types**: Use type annotations and be specific about parameter and return types in the docstrings.
1. **Document exceptions**: If your function can raise exceptions, document them in the "Raises" section.
1. **Use consistent formatting**: Follow the Google style format consistently across all docstrings.
1. **Group related functions**: In module docstrings, group related functions together to help users understand the organization of the module.
1. **Include context**: Provide context about how the function or class fits into the larger system.

## Testing Documentation

You can test how your docstrings will be rendered in the documentation by building the documentation site locally:

```bash
# Install MkDocs and plugins
pip install mkdocs mkdocstrings[python] mkdocs-material

# Build the documentation
mkdocs build

# Serve the documentation locally
mkdocs serve
```

Then open your browser to http://localhost:8000 to view the documentation site.

## Additional Resources

- [Google Python Style Guide - Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [mkdocstrings Documentation](https://mkdocstrings.github.io/)
- [MkDocs Documentation](https://www.mkdocs.org/)
