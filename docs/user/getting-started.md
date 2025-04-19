# Getting Started with Conda-Forge Converter

A tool for converting Anaconda environments to conda-forge and validating GitHub Actions workflows.

## Requirements

- Python 3.11 or later
- Git (for development)

## Installation

### Using UV (Recommended)

UV is a modern Python package installer that offers better performance and dependency resolution:

```bash
# Install UV if you haven't already
python -m pip install uv

# Install conda-forge-converter
uv pip install conda-forge-converter
```

### Using Pip

```bash
pip install conda-forge-converter
```

### Development Installation

For development, you'll want to install additional dependencies:

```bash
# Clone the repository
git clone https://github.com/ricea/anaconda-to-miniconda2
cd anaconda-to-miniconda2

# Install with development dependencies using UV
uv pip install -e ".[dev,test]"

# Set up pre-commit hooks
pre-commit install
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

## Configuration

The tool uses sensible defaults but can be configured through:

1. Environment variables
1. Configuration file (`~/.config/conda-forge-converter/config.yml`)
1. Command-line arguments

For detailed configuration options, see the [CLI Reference](cli-reference.md).

## Troubleshooting

### Common Issues

1. **Package Conflicts**: If you see dependency conflicts, try:

   ```bash
   uv pip install --upgrade conda-forge-converter
   ```

1. **Permission Issues**: On Unix-like systems, you might need to use:

   ```bash
   sudo uv pip install conda-forge-converter
   ```

1. **Python Version**: If you get a Python version error:

   ```bash
   pyenv install 3.11
   pyenv global 3.11
   uv pip install conda-forge-converter
   ```

### Getting Help

- Check our [FAQ](faq.md)
- [Open an issue](https://github.com/ricea/anaconda-to-miniconda2/issues)
- [Join our discussions](https://github.com/ricea/anaconda-to-miniconda2/discussions)

## Why Use conda-forge?

- 🏢 Community-maintained packages
- 🔄 More up-to-date package versions
- 🧩 Better dependency resolution
- 📚 Broader package selection
- 🛠️ Active maintenance and support
