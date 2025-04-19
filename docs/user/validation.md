# Environment Validation

The conda-forge-converter includes a comprehensive validation framework to help ensure that converted environments are functioning correctly. This guide explains how to use the validation tools to verify your converted environments.

## Overview

The validation framework provides several ways to validate converted environments:

1. **Package Validation**: Checks if packages are installed and importable
1. **Environment Comparison**: Compares source and target environments
1. **Custom Validation Scripts**: Run custom validation code in the environment
1. **Python Compatibility Tests**: Verify Python compatibility

## Using the Validation Framework

### Basic Environment Validation

To validate a converted environment, use the `validate_converted_env.py` script:

```bash
python -m conda_forge_converter.examples.validate_converted_env my_converted_env
```

This will:

- Check if all packages are installed
- Verify that packages can be imported
- Provide a summary of validation results

### Comparing with Source Environment

To compare a converted environment with its source environment:

```bash
python -m conda_forge_converter.examples.validate_converted_env my_converted_env --source-env my_original_env
```

This will show:

- Packages that exist in both environments
- Packages that only exist in the source environment
- Packages that only exist in the target environment
- Version differences between environments

### Running Custom Validation Scripts

You can run custom validation scripts in the environment:

```bash
python -m conda_forge_converter.examples.validate_converted_env my_converted_env --script my_validation_script.py
```

### Saving Validation Results

To save validation results to a JSON file:

```bash
python -m conda_forge_converter.examples.validate_converted_env my_converted_env --output validation_results.json
```

## Creating Custom Validation Scripts

You can create custom validation scripts to test specific functionality in your environment. The `validation_script_template.py` provides a starting point:

```bash
cp conda_forge_converter/examples/validation_script_template.py my_validation_script.py
```

Edit the script to include your specific validation requirements:

1. Define packages to validate
1. Specify version requirements
1. Add custom functionality tests

### Example Validation Script

```python
#!/usr/bin/env python
"""Custom validation script for my environment."""

import importlib
import sys
from typing import Dict, List, Tuple


def validate_imports(packages: List[str]) -> Tuple[bool, Dict[str, str]]:
    """Validate that packages can be imported."""
    # Implementation...


def validate_package_versions(
    version_checks: Dict[str, str],
) -> Tuple[bool, Dict[str, str]]:
    """Validate package versions."""
    # Implementation...


def run_functionality_tests() -> Tuple[bool, Dict[str, str]]:
    """Run functionality tests for key packages."""
    # Implementation...


def main() -> int:
    """Run the validation script."""
    # Define packages to validate
    packages_to_validate = [
        "numpy",
        "pandas",
        "matplotlib",
        # Add your packages here
    ]

    # Define version requirements
    version_requirements = {
        "numpy": "1.20.0",
        "pandas": "1.3.0",
        # Add your version requirements here
    }

    # Run validation steps...

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
```

## Programmatic Validation

You can also use the validation framework programmatically in your own code:

```python
from conda_forge_converter.validation import ValidationFramework

# Create validation framework
framework = ValidationFramework(verbose=True)

# Validate an environment
result = framework.validate_environment("my_converted_env", "my_original_env")

# Check if validation passed
if result.passed:
    print("Validation passed!")
else:
    print(f"Validation failed: {result.message}")

# Access detailed results
print(f"Total packages: {result.details['total_packages']}")
print(f"Installed packages: {result.details['installed_packages']}")
print(f"Importable packages: {result.details['importable_packages']}")

# Run a validation script
script_result = framework.run_validation_script(
    "my_converted_env", "my_validation_script.py"
)
```

## Troubleshooting

If validation fails, check the following:

1. **Missing Packages**: Ensure all required packages are installed
1. **Import Errors**: Check for compatibility issues or missing dependencies
1. **Version Mismatches**: Verify that package versions meet your requirements
1. **Functionality Tests**: Debug any failing functionality tests

For more help, see the [Troubleshooting Guide](troubleshooting.md).
