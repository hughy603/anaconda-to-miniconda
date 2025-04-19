# CLI Module

The CLI module provides the command-line interface for the conda-forge-converter tool. It handles argument parsing, command execution, and orchestrates the entire conversion process.

## Overview

The CLI module is the main entry point for the conda-forge-converter tool. It provides a comprehensive command-line interface with various commands and options for converting Anaconda environments to conda-forge environments, checking environment health, generating reports, and updating existing environments.

## API Reference

::: conda_forge_converter.cli
options:
show_source: true
show_root_heading: true
show_category_heading: true
members_order: source

## Command-Line Interface

The CLI provides several commands and options:

### Main Commands

- **Default**: Convert a single environment or batch of environments
- **help**: Show detailed help with examples and workflows
- **health**: Check the health of a conda environment
- **report**: Generate a detailed report about a conversion
- **update**: Update an existing conda-forge environment

### Single Environment Conversion

```bash
conda-forge-converter -s myenv -t myenv_forge
```

### Batch Conversion

```bash
conda-forge-converter --batch --pattern 'data*'
```

### Health Check

```bash
conda-forge-converter health myenv --verify
```

### Report Generation

```bash
conda-forge-converter report --source myenv --target myenv_forge --output report.json
```

### Environment Update

```bash
conda-forge-converter update myenv_forge --all
```

## Integration with Other Modules

The CLI module integrates with other modules in the package:

- **core**: For environment conversion functionality
- **health**: For environment health checking
- **incremental**: For updating existing environments
- **reporting**: For generating reports
- **utils**: For logging and utility functions

## Error Handling

The CLI module handles errors gracefully, logging appropriate error messages and returning appropriate exit codes. It does not raise exceptions directly; all errors are logged and reflected in the return code.
