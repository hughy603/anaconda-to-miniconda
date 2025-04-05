# API Reference

This section provides detailed documentation for the Conda-Forge Converter Python API. The API is designed for developers who want to integrate the conversion functionality into their own applications or scripts.

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
from conda_forge_converter.core import EnvironmentConverter

# Create a converter
converter = EnvironmentConverter()

# Convert an environment
converter.convert_environment("myenv", "myenv_forge")
```

### CLI Module

The [cli module](cli.md) provides the command-line interface for the tool. It handles argument parsing and command execution.

```python
from conda_forge_converter.cli import parse_args, run_command

# Parse arguments
args = parse_args(["--source-env", "myenv", "--target-env", "myenv_forge"])

# Run command with parsed arguments
run_command(args)
```

### Health Module

The [health module](health.md) analyzes environments for potential issues.

```python
from conda_forge_converter.health import HealthChecker

# Create a health checker
checker = HealthChecker()

# Check an environment
report = checker.check_environment("myenv")
```

### Reporting Module

The [reporting module](reporting.md) generates reports about conversions.

```python
from conda_forge_converter.reporting import ReportGenerator

# Create a report generator
generator = ReportGenerator()

# Generate a report
report = generator.generate_report("myenv", "myenv_forge")
```

### Incremental Module

The [incremental module](incremental.md) handles updating existing conda-forge environments.

```python
from conda_forge_converter.incremental import IncrementalUpdater

# Create an incremental updater
updater = IncrementalUpdater()

# Update an environment
updater.update_environment("myenv_forge")
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
from conda_forge_converter.core import EnvironmentConverter
from conda_forge_converter.exceptions import EnvironmentNotFoundError

converter = EnvironmentConverter()

try:
    converter.convert_environment("myenv", "myenv_forge")
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
