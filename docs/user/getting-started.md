# Getting Started with Conda-Forge Converter

A simple tool to convert Anaconda environments to conda-forge environments.

## Installation

```bash
pip install conda-forge-converter
```

## Basic Usage

### Converting a Single Environment

```bash
conda-forge-converter -s myenv -t myenv_forge
```

Where:

- `-s, --source-env`: Your existing Anaconda environment
- `-t, --target-env`: Your new conda-forge environment

### Specifying Python Version

```bash
conda-forge-converter -s myenv -t myenv_forge --python 3.11
```

### Preview Mode

To see what would happen without making any changes:

```bash
conda-forge-converter -s myenv -t myenv_forge --dry-run
```

## Batch Conversion

Convert multiple environments at once:

```bash
conda-forge-converter --batch
```

This will find all conda environments and convert them, adding a "\_forge" suffix to each.

### Pattern Matching

Convert only environments matching specific patterns:

```bash
conda-forge-converter --batch --pattern "data*" --exclude "test_env"
```

## Why Use conda-forge?

- Community-maintained packages
- More up-to-date package versions
- Better dependency resolution
- Broader package selection
