# CLI Quick Reference

This quick reference provides commonly used commands for the conda-forge-converter tool. Use it as a handy cheat sheet for day-to-day operations.

## Basic Commands

| Command | Description |
| ----------------------------------------------------- | ---------------------------------------------- |
| `conda-forge-converter --help` | Display help information |
| `conda-forge-converter --version` | Display version information |
| `conda-forge-converter -s SOURCE -t TARGET` | Convert a single environment |
| `conda-forge-converter --batch` | Convert all environments |
| `conda-forge-converter --dry-run -s SOURCE -t TARGET` | Show what would be done without making changes |

## Common Use Cases

### Converting a Single Environment

```bash
# Basic conversion
conda-forge-converter -s myenv -t myenv_forge

# With verbose output
conda-forge-converter -s myenv -t myenv_forge --verbose

# With specific Python version
conda-forge-converter -s myenv -t myenv_forge --python-version 3.10

# Dry run (no changes made)
conda-forge-converter -s myenv -t myenv_forge --dry-run
```

### Batch Conversion

```bash
# Convert all environments
conda-forge-converter --batch

# Convert environments matching a pattern
conda-forge-converter --batch --pattern 'data*'

# Dry run batch conversion
conda-forge-converter --batch --pattern 'data*' --dry-run
```

### System Administrator Tasks

```bash
# Convert environment as root (preserves ownership)
sudo conda-forge-converter -s /home/user/anaconda3/envs/myenv -t myenv_forge

# Convert without preserving ownership
sudo conda-forge-converter -s myenv -t myenv_forge --no-preserve-ownership

# Batch convert all user environments
sudo conda-forge-converter --batch
```

## Options Reference

| Option | Description | Default |
| ------------------------- | ------------------------------------------------------------------ | -------------- |
| `-s, --source` | Source environment name or path | (required) |
| `-t, --target` | Target environment name | (required) |
| `--python-version` | Python version for new environment | Same as source |
| `--dry-run` | Show what would be done without making changes | `False` |
| `--verbose` | Show detailed output | `False` |
| `--batch` | Convert multiple environments | `False` |
| `--pattern` | Pattern to match environment names when using --batch | `*` |
| `--no-preserve-ownership` | Don't preserve original environment ownership when running as root | `False` |
| `--use-fast-solver` | Use libmamba solver for faster dependency resolution | `True` |
| `--batch-size` | Number of packages to install in a batch | `20` |

## Environment Variables

| Variable | Description | Default |
| ---------------------------------- | ------------------------------------------- | -------------------------------- |
| `CONDA_FORGE_CONVERTER_CACHE_DIR` | Directory for caching package metadata | `~/.cache/conda-forge-converter` |
| `CONDA_FORGE_CONVERTER_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `CONDA_FORGE_CONVERTER_TIMEOUT` | Timeout for network operations (seconds) | `60` |
| `CONDA_FORGE_CONVERTER_BATCH_SIZE` | Number of packages to install in a batch | `20` |

## Common Error Messages and Solutions

| Error | Solution |
| -------------------------- | ------------------------------------------------------------------------- |
| `EnvironmentNotFoundError` | Check that the source environment exists |
| `EnvironmentExistsError` | Choose a different target environment name or remove the existing one |
| `PackageNotFoundError` | Some packages may not be available in conda-forge; check logs for details |
| `PermissionError` | Run with sudo or check file permissions |
| `NetworkError` | Check internet connection or try again later |

## Tips and Tricks

- Use `--verbose` for detailed output when troubleshooting
- Use `--dry-run` to preview changes before making them
- When converting many environments, use `--batch` with `--pattern` to target specific ones
- For large environments, increase batch size with `--batch-size 50` for faster installation
- Set `CONDA_FORGE_CONVERTER_LOG_LEVEL=DEBUG` for maximum logging detail
