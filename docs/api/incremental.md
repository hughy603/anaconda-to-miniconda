# Incremental Module

The Incremental module provides functionality for updating existing conda-forge environments and detecting drift between environments.

## Overview

This module contains functions for updating existing conda-forge environments and detecting drift between source and target environments. It allows for incremental updates to environments rather than full conversions, which can be more efficient for maintaining environments over time.

## API Reference

::: conda_forge_converter.incremental
options:
show_source: true
show_root_heading: true
show_category_heading: true
members_order: source

## Usage Examples

### Update Environment

```python
from conda_forge_converter.incremental import update_conda_forge_environment

# Update all packages in an environment
result = update_conda_forge_environment("myenv_forge", update_all=True)

# Update specific packages
result = update_conda_forge_environment(
    "myenv_forge", specific_packages=["numpy", "pandas"]
)

# Add missing packages from source environment
result = update_conda_forge_environment("myenv_forge", add_missing=True)
```

### Detect Drift

```python
from conda_forge_converter.incremental import detect_drift

# Detect drift between environments
drift_result = detect_drift("myenv_forge")

# Print drift information
print(f"Source packages: {drift_result['source_package_count']}")
print(f"Target packages: {drift_result['target_package_count']}")
print(f"Same versions: {len(drift_result['same_versions'])}")
print(f"Different versions: {len(drift_result['different_versions'])}")
print(f"Only in source: {len(drift_result['source_only'])}")
print(f"Only in target: {len(drift_result['target_only'])}")
print(f"Environment similarity: {drift_result['environment_similarity']}%")
```

## Usage in the CLI

The Incremental module is used by the CLI module to provide the `update` command:

```bash
# Detect drift between environments
conda-forge-converter update myenv_forge --drift

# Update all outdated packages
conda-forge-converter update myenv_forge --all

# Update specific packages
conda-forge-converter update myenv_forge --packages numpy pandas matplotlib

# Add missing packages from source
conda-forge-converter update myenv_forge --add-missing

# Save update report
conda-forge-converter update myenv_forge --all --report update_report.json
```

## Update Process

The update process typically includes:

1. **Environment Analysis**: Analyzing the target environment and its source
1. **Package Selection**: Determining which packages to update based on options
1. **Package Updates**: Updating selected packages to their latest versions
1. **Missing Package Addition**: Adding packages that exist in source but not in target
1. **Verification**: Verifying that the environment still functions correctly

## Drift Analysis

The drift analysis process typically includes:

1. **Environment Identification**: Identifying the source environment based on naming convention
1. **Package Comparison**: Comparing packages and versions between environments
1. **Similarity Calculation**: Calculating the similarity percentage between environments
1. **Drift Reporting**: Generating a report of the drift analysis

## Integration with Other Modules

The Incremental module integrates with:

- **core**: For accessing environment information
- **utils**: For running commands and logging
- **reporting**: For generating reports about updates
