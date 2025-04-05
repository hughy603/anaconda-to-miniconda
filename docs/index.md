# Conda-Forge Converter

A tool to convert Anaconda environments to conda-forge environments.

## Overview

This tool helps migrate from Anaconda to conda-forge by:

1. Detecting existing Anaconda environments
1. Creating new conda-forge environments with the same packages
1. Supporting both conda and pip packages
1. Verifying environment health

## Navigation

- [Getting Started](user/getting-started.md)
- [CLI Reference](user/cli-reference.md)
- [Common Workflows](user/workflows.md)
- [Troubleshooting](user/troubleshooting.md)

## Why Use conda-forge?

- Community-maintained packages
- More up-to-date package versions
- Better dependency resolution
- Broader package selection

## Quick Start

```bash
# Install the package
pip install conda-forge-converter

# Convert a single environment
conda-forge-converter -s myenv -t myenv_forge

# Batch convert environments
conda-forge-converter --batch --pattern "data*"
```

See the [CLI Reference](user/cli-reference.md) for all available options.
