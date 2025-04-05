# Core Module API

The `core` module contains the main functionality for converting Anaconda environments to conda-forge environments.

## EnvironmentConverter

The primary class for converting environments.

```python
from conda_forge_converter.core import EnvironmentConverter

converter = EnvironmentConverter()
converter.convert_environment("myenv", "myenv_forge")
```

### Constructor

```python
EnvironmentConverter(logger=None)
```

**Parameters:**

- `logger`: Optional logger instance. If not provided, a default logger is created.

### Methods

#### convert_environment

```python
def convert_environment(self, source_env, target_env, python=None,
                       dry_run=False, health_check=False, verify=False,
                       generate_report=None, **kwargs)
```

Converts an Anaconda environment to a conda-forge environment.

**Parameters:**

- `source_env`: Name of the source Anaconda environment
- `target_env`: Name for the new conda-forge environment
- `python`: Python version for the new environment (default: same as source)
- `dry_run`: Show what would be done without making changes
- `health_check`: Run health check before and after conversion
- `verify`: Verify target environment functionality after conversion
- `generate_report`: Path to save conversion report
- `**kwargs`: Additional keyword arguments

**Returns:**

- Dictionary with conversion results

**Raises:**

- `EnvironmentNotFoundError`: If source environment not found
- `PackageInstallationError`: If package installation fails
- `ConversionError`: For other conversion errors

#### batch_convert

```python
def batch_convert(self, pattern=None, exclude=None, target_suffix="_forge",
                 max_parallel=1, search_path=None, search_depth=3, **kwargs)
```

Converts multiple environments in batch mode.

**Parameters:**

- `pattern`: Pattern for matching environment names (e.g., 'data\*')
- `exclude`: Comma-separated list of environments to exclude
- `target_suffix`: Suffix to add to target environment names
- `max_parallel`: Maximum number of parallel conversions
- `search_path`: Path to search for conda environments
- `search_depth`: Maximum directory depth when searching
- `**kwargs`: Additional arguments passed to convert_environment

**Returns:**

- Dictionary with batch conversion results

## Functions

### discover_environments

```python
def discover_environments(search_path=None, search_depth=3)
```

Finds conda environments on the system.

**Parameters:**

- `search_path`: Path to search for conda environments
- `search_depth`: Maximum directory depth when searching

**Returns:**

- Dictionary of environment names to their paths

### extract_packages

```python
def extract_packages(env_data)
```

Extracts package information from environment data.

**Parameters:**

- `env_data`: Environment data from conda env export

**Returns:**

- Dictionary of package names to their versions

### separate_conda_pip_packages

```python
def separate_conda_pip_packages(packages)
```

Separates conda and pip packages.

**Parameters:**

- `packages`: Dictionary of package names to versions

**Returns:**

- Tuple of (conda_packages, pip_packages)

### create_environment

```python
def create_environment(name, packages, python=None, pip_packages=None,
                      channels=["conda-forge"], dry_run=False)
```

Creates a new conda environment with specified packages.

**Parameters:**

- `name`: Name for the new environment
- `packages`: Dictionary of conda package names to versions
- `python`: Python version for the new environment
- `pip_packages`: Dictionary of pip package names to versions
- `channels`: List of conda channels to use
- `dry_run`: Show what would be done without making changes

**Returns:**

- Path to the created environment

## Examples

### Basic Conversion

```python
from conda_forge_converter.core import EnvironmentConverter

# Create converter
converter = EnvironmentConverter()

# Convert environment
result = converter.convert_environment(source_env="myenv", target_env="myenv_forge")

print(f"Conversion successful: {result['success']}")
print(f"Packages installed: {len(result['packages'])}")
```

### Dry Run

```python
# Preview conversion without making changes
result = converter.convert_environment(
    source_env="myenv", target_env="myenv_forge", dry_run=True
)

print("Packages that would be installed:")
for package, version in result["packages"].items():
    print(f"  {package}={version}")
```

### Batch Conversion

```python
# Convert all data-related environments
results = converter.batch_convert(pattern="data*", exclude="test_*", max_parallel=4)

print(f"Successful conversions: {len(results['successful'])}")
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
