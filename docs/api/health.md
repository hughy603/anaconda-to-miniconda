# Health Module

The Health module provides functionality for analyzing and verifying conda environments for potential issues.

## Overview

This module contains functions for checking the health of conda environments and verifying their functionality. It helps identify potential issues with environments before and after conversion.

## API Reference

::: conda_forge_converter.health
options:
show_source: true
show_root_heading: true
show_category_heading: true
members_order: source

## Usage Examples

### Check Environment Health

```python
from conda_forge_converter.health import check_environment_health

# Check an environment
health_result = check_environment_health("myenv")

# Print the status
print(f"Environment status: {health_result['status']}")

# Print any issues
for issue in health_result.get("issues", []):
    print(f"- {issue}")
```

### Verify Environment Functionality

```python
from conda_forge_converter.health import verify_environment

# Verify an environment
if verify_environment("myenv_forge"):
    print("Environment verification passed")
else:
    print("Environment verification failed")
```

## Usage in the CLI

The Health module is used by the CLI module to provide the `health` command and the `--health-check` and `--verify` options:

```bash
# Check environment health
conda-forge-converter health myenv

# Verify environment functionality
conda-forge-converter health myenv --verify

# Include health check during conversion
conda-forge-converter -s myenv -t myenv_forge --health-check

# Verify target environment after conversion
conda-forge-converter -s myenv -t myenv_forge --verify
```

## Health Check Process

The health check process typically includes:

1. **Package Inventory**: Listing all installed packages and their versions
1. **Dependency Analysis**: Checking for missing or conflicting dependencies
1. **Environment Structure**: Verifying the environment's directory structure
1. **Python Functionality**: Testing basic Python functionality
1. **Package Imports**: Attempting to import key packages

## Verification Process

The verification process typically includes:

1. **Basic Tests**: Running basic tests to ensure the environment works
1. **Package Tests**: Testing key packages to ensure they function correctly
1. **Integration Tests**: Testing how packages work together

## Integration with Other Modules

The Health module integrates with:

- **core**: For accessing environment information
- **utils**: For running commands and logging
