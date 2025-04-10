# Conda-Forge Converter CLI Cheat Sheet

## Basic Commands

```bash
# Get help
conda-forge-converter --help

# Check version
conda-forge-converter --version

# Convert a single environment
conda-forge-converter -s SOURCE_ENV -t TARGET_ENV

# Convert with verbose output
conda-forge-converter -s SOURCE_ENV -t TARGET_ENV --verbose

# Dry run (no changes)
conda-forge-converter -s SOURCE_ENV -t TARGET_ENV --dry-run

# Specify Python version
conda-forge-converter -s SOURCE_ENV -t TARGET_ENV --python-version 3.10
```

## Batch Operations

```bash
# Convert all environments
conda-forge-converter --batch

# Convert environments matching pattern
conda-forge-converter --batch --pattern 'data*'

# Batch with dry run
conda-forge-converter --batch --pattern 'data*' --dry-run
```

## System Administrator Commands

```bash
# Run as root (preserves ownership)
sudo conda-forge-converter -s SOURCE_ENV -t TARGET_ENV

# Run as root without preserving ownership
sudo conda-forge-converter -s SOURCE_ENV -t TARGET_ENV --no-preserve-ownership

# Batch convert as root
sudo conda-forge-converter --batch
```

## Performance Options

```bash
# Use fast solver (default)
conda-forge-converter -s SOURCE_ENV -t TARGET_ENV --use-fast-solver

# Increase batch size
conda-forge-converter -s SOURCE_ENV -t TARGET_ENV --batch-size 50

# Set cache directory
export CONDA_FORGE_CONVERTER_CACHE_DIR=/path/to/cache
conda-forge-converter -s SOURCE_ENV -t TARGET_ENV
```

## Environment Variables

```bash
# Set cache directory
export CONDA_FORGE_CONVERTER_CACHE_DIR=/path/to/cache

# Set log level
export CONDA_FORGE_CONVERTER_LOG_LEVEL=DEBUG

# Set network timeout
export CONDA_FORGE_CONVERTER_TIMEOUT=120

# Set batch size
export CONDA_FORGE_CONVERTER_BATCH_SIZE=50
```

## Common Patterns

```bash
# Convert and test
conda-forge-converter -s myenv -t myenv_forge
conda activate myenv_forge
# Run your tests here

# Convert multiple environments with specific pattern
conda-forge-converter --batch --pattern 'project_*'

# Convert environment with specific Python version
conda-forge-converter -s myenv -t myenv_forge --python-version 3.9
```

## Troubleshooting Commands

```bash
# Verbose output
conda-forge-converter -s myenv -t myenv_forge --verbose

# Check environment list
conda env list

# Check package list in environment
conda list -n myenv

# Check conda configuration
conda config --show

# Check permissions (Linux/macOS)
ls -la $(conda info --base)/envs/
```
