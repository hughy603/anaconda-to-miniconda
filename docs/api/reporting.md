# Reporting Module

The Reporting module provides functionality for generating reports about environment conversions.

## Overview

This module contains functions for generating detailed reports about environment conversions, including information about packages, conversion success, and other metrics. These reports can be used to analyze the conversion process and identify any issues.

## API Reference

::: conda_forge_converter.reporting
options:
show_source: true
show_root_heading: true
show_category_heading: true
members_order: source

## Usage Examples

### Generate Conversion Report

```python
from conda_forge_converter.reporting import generate_conversion_report

# Generate a report
report = generate_conversion_report(
    "myenv", "myenv_forge", True, "report.json", verbose=True
)

# Access report data
print(f"Conversion success: {report['success']}")
print(f"Total packages: {report['package_count']}")
```

### Generate Summary Report

```python
from conda_forge_converter.reporting import generate_summary_report

# Generate a summary report
summary = generate_summary_report(batch_results, "summary.json")

# Access summary data
print(f"Total environments: {summary['total_environments']}")
print(f"Successful conversions: {summary['successful_conversions']}")
print(f"Failed conversions: {summary['failed_conversions']}")
```

### Print Report Summary

```python
from conda_forge_converter.reporting import (
    generate_conversion_report,
    print_report_summary,
)

# Generate a report
report = generate_conversion_report("myenv", "myenv_forge", True)

# Print a summary
print_report_summary(report)
```

## Report Structure

### Conversion Report

A typical conversion report includes:

- **Metadata**:

  - `timestamp`: When the report was generated
  - `source_env`: Name of the source environment
  - `target_env`: Name of the target environment
  - `success`: Whether the conversion was successful

- **Package Information**:

  - `package_count`: Total number of packages
  - `packages`: Detailed information about each package
  - `same_versions`: Packages with the same version in both environments
  - `different_versions`: Packages with different versions
  - `source_only`: Packages only in the source environment
  - `target_only`: Packages only in the target environment

- **Performance Metrics**:

  - `conversion_time`: Time taken for the conversion
  - `package_installation_time`: Time taken for package installation

- **Issues**:

  - `errors`: Any errors encountered during conversion
  - `warnings`: Any warnings generated during conversion

### Summary Report

A typical summary report includes:

- **Overall Statistics**:

  - `total_environments`: Total number of environments processed
  - `successful_conversions`: Number of successful conversions
  - `failed_conversions`: Number of failed conversions
  - `success_rate`: Percentage of successful conversions

- **Common Issues**:

  - `common_errors`: Frequently encountered errors
  - `common_warnings`: Frequently encountered warnings

- **Performance Metrics**:

  - `total_conversion_time`: Total time taken for all conversions
  - `average_conversion_time`: Average time per conversion

## Usage in the CLI

The Reporting module is used by the CLI module to provide the `report` command and the `--generate-report` option:

```bash
# Generate a report for existing environments
conda-forge-converter report --source myenv --target myenv_forge --output report.json

# Print a summary of the report
conda-forge-converter report --source myenv --target myenv_forge --output report.json --print

# Generate a report during conversion
conda-forge-converter -s myenv -t myenv_forge --generate-report report.json
```

## Integration with Other Modules

The Reporting module integrates with:

- **core**: For accessing environment information
- **utils**: For logging and file operations
