# Troubleshooting Guide

Common issues and solutions when using Conda-Forge Converter.

## Environment Not Found

**Problem:** Error message: `Environment 'myenv' not found`

**Fix:**

- Check if the environment exists with `conda env list`
- Verify the environment name spelling
- Specify a search path if needed: `conda-forge-converter -s myenv -t myenv_forge --search-path /path/to/envs`

## Package Installation Failures

**Problem:** Error like `PackagesNotFoundError` during installation

**Fix:**

- Check if the package is on conda-forge: `conda search -c conda-forge package_name`
- Try running with verbose logging: `conda-forge-converter -s myenv -t myenv_forge -v`

## Dependency Conflicts

**Problem:** Error about package conflicts

**Fix:**

- Run health check: `conda-forge-converter health myenv`
- Create environment with only core packages first, then add others

## Disk Space Issues

**Problem:** Error about insufficient disk space

**Fix:**

- Remove unused environments: `conda env remove -n unused_env`
- Clear conda cache: `conda clean --all`

## Logging and Debugging

For detailed troubleshooting:

```bash
conda-forge-converter -s myenv -t myenv_forge -v --log-file debug.log
```

## Getting Help

If you need additional help:

1. Check the GitHub repository for similar issues
1. Include command used, error message, and output of `conda info`
