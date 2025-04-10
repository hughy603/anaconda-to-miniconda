# API Reference

This section provides detailed documentation for the Conda-Forge Converter Python API. The API is designed for developers who want to integrate the conversion functionality into their own applications or scripts.

## Documentation Approach

The Conda-Forge Converter uses docstring-driven documentation. All API documentation is generated directly from the docstrings in the source code, ensuring that the documentation is always up-to-date with the code. The docstrings follow the Google style format and include detailed descriptions, parameter information, return values, examples, and notes where applicable.

## Package Structure

The Conda-Forge Converter package is organized into several modules:

- **core**: Main conversion functionality
- **cli**: Command-line interface
- **health**: Environment health checking
- **reporting**: Report generation
- **incremental**: Incremental updates
- **utils**: Utility functions

## Module Overview

### Core Module

The [core module](core.md) contains the main functionality for converting environments. It handles environment discovery, package analysis, and environment creation.

```python
from conda_forge_converter.core import convert_environment

# Convert an environment
convert_environment("myenv", "myenv_forge")
```

### CLI Module

The [cli module](cli.md) provides the command-line interface for the tool. It handles argument parsing and command execution.

```python
from conda_forge_converter.cli import parse_args, main

# Parse arguments
args = parse_args(["--source-env", "myenv", "--target-env", "myenv_forge"])

# Run command with parsed arguments
exit_code = main(["--source-env", "myenv", "--target-env", "myenv_forge"])
```

### Health Module

The [health module](health.md) analyzes environments for potential issues.

```python
from conda_forge_converter.health import check_environment_health

# Check an environment
report = check_environment_health("myenv")
```

### Reporting Module

The [reporting module](reporting.md) generates reports about conversions.

```python
from conda_forge_converter.reporting import generate_conversion_report

# Generate a report
report = generate_conversion_report("myenv", "myenv_forge", True, "report.json")
```

### Incremental Module

The [incremental module](incremental.md) handles updating existing conda-forge environments.

```python
from conda_forge_converter.incremental import update_conda_forge_environment

# Update an environment
update_conda_forge_environment("myenv_forge", update_all=True)
```

### Utils Module

The [utils module](utils.md) contains utility functions used across the package.

```python
from conda_forge_converter.utils import run_command, check_disk_space

# Run a shell command
result = run_command(["conda", "env", "list"])

# Check available disk space
space_available = check_disk_space("/path/to/dir")
```

## Error Handling

All API functions use Python's native exception system. Common exceptions include:

- `EnvironmentNotFoundError`: Environment not found
- `PackageInstallationError`: Package installation failed
- `VerificationError`: Environment verification failed

Example error handling:

```python
from conda_forge_converter.core import convert_environment
from conda_forge_converter.exceptions import EnvironmentNotFoundError

try:
    convert_environment("myenv", "myenv_forge")
except EnvironmentNotFoundError:
    print("Environment not found")
except Exception as e:
    print(f"Conversion failed: {e}")
```

## Type Annotations

All API functions include type annotations for better IDE support and static type checking:

```python
def extract_packages(env_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract packages from environment data.

    Args:
        env_data: Environment data

    Returns:
        Dictionary of package names to versions
    """
    # Implementation...
```
