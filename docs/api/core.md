# Core Module API

The `core` module contains the main functionality for converting Anaconda environments to conda-forge environments.

## Overview

This module provides classes and functions for environment discovery, package analysis, and environment creation. It is the heart of the conda-forge-converter package, handling the actual conversion process.

## API Reference

::: conda_forge_converter.core
options:
show_source: true
show_root_heading: true
show_category_heading: true
members_order: source

## Examples

### Basic Conversion

```python
from conda_forge_converter.core import convert_environment

# Convert environment
result = convert_environment(source_env="myenv", target_env="myenv_forge")

print(f"Conversion successful: {result['success']}")
print(f"Packages installed: {len(result['packages'])}")
```

### Dry Run

```python
# Preview conversion without making changes
result = convert_environment(source_env="myenv", target_env="myenv_forge", dry_run=True)

print("Packages that would be installed:")
for package, version in result["packages"].items():
    print(f"  {package}={version}")
```

### Batch Conversion

```python
from conda_forge_converter.core import convert_multiple_environments

# Convert all data-related environments
results = convert_multiple_environments(
    env_pattern="data*", exclude="test_*", max_parallel=4
)

print(f"Successful conversions: {len(results['success'])}")
print(f"Failed conversions: {len(results['failed'])}")
```

### Custom Environment Discovery

```python
from conda_forge_converter.core import discover_environments

# Find environments in a custom path
envs = discover_environments(search_path="/path/to/conda/envs")

for name, path in envs.items():
    print(f"Found environment '{name}' at {path}")
```
