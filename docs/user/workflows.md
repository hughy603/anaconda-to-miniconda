# Common Workflows

Essential workflows for using Conda-Forge Converter.

## Single Environment Conversion

```bash
# Basic conversion
conda-forge-converter -s myenv -t myenv_forge

# With health check
conda-forge-converter -s myenv -t myenv_forge --health-check

# With specific Python version
conda-forge-converter -s myenv -t myenv_forge --python 3.11

# Preview only (no changes)
conda-forge-converter -s myenv -t myenv_forge --dry-run
```

## Batch Environment Conversion

```bash
# Convert all environments
conda-forge-converter --batch

# Convert environments matching a pattern
conda-forge-converter --batch --pattern "data*"

# Exclude specific environments
conda-forge-converter --batch --exclude "test_env,dev_env"

# With custom suffix
conda-forge-converter --batch --target-suffix "_cf"
```

## Environment Health Checks

```bash
# Check environment health
conda-forge-converter health myenv

# With verification
conda-forge-converter health myenv --verify

# Generate a report
conda-forge-converter health myenv --output health_report.json
```

## Update Existing Environments

```bash
# Add missing packages
conda-forge-converter update myenv_forge --add-missing

# Update all packages
conda-forge-converter update myenv_forge --all

# Update specific packages
conda-forge-converter update myenv_forge --packages numpy,pandas
```
