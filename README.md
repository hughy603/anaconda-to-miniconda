# conda-forge-converter

A tool to convert Anaconda environments to conda-forge environments with the same top-level dependency versions.

## Features

- Convert single or multiple conda environments to use conda-forge channels
- Preserve exact package versions during conversion
- Discover environments in custom paths on your system
- Support for both conda and pip packages within environments
- Parallel processing for batch conversions
- Automatic backups of environment specifications
- Disk space estimation before conversion
- Pattern matching for selective batch conversions

## Installation

### Using uv (Recommended)

```bash
uv pip install conda-forge-converter
```

### Using pip

```bash
pip install conda-forge-converter
```

### From source

```bash
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter
pip install -e .
```

## Usage

### Converting a Single Environment

To convert a single environment:

```bash
conda-forge-converter -s myenv -t myenv_forge
```

This will create a new environment called `myenv_forge` with the same packages as `myenv`, but using conda-forge as the source channel.

### Batch Converting Multiple Environments

To convert all environments:

```bash
conda-forge-converter --batch
```

This will create new environments with "_forge" suffix for each existing environment.

### Filtering Environments

To convert only environments matching a pattern:

```bash
conda-forge-converter --batch --pattern "data*" --exclude "data_test,data_old"
```

### Search for Environments in Custom Paths

```bash
conda-forge-converter --batch --search-path /opt/conda_envs --search-path /home/user/envs
```

### Preview Without Creating Environments

```bash
conda-forge-converter --batch --dry-run
```

### Parallel Conversion

```bash
conda-forge-converter --batch --max-parallel 4
```

## Options

```
-s, --source-env SOURCE_ENV  Name of the source Anaconda environment
-t, --target-env TARGET_ENV  Name for the new conda-forge environment
--batch                       Convert multiple environments
--pattern PATTERN             Pattern for matching environment names (e.g., 'data*')
--exclude EXCLUDE             Comma-separated list of environments to exclude
--target-suffix TARGET_SUFFIX Suffix to add to target environment names (default: _forge)
--search-path SEARCH_PATH     Path to search for conda environments (can be specified multiple times)
--search-depth SEARCH_DEPTH   Maximum directory depth when searching for environments (default: 3)
--max-parallel MAX_PARALLEL   Maximum number of parallel conversions (default: 1)
--no-backup                   Skip backing up environment specifications
--python PYTHON               Specify Python version for the new environment
--dry-run                     Show what would be installed without creating environments
--verbose, -v                 Show detailed output of conda commands
--log-file LOG_FILE           Path to log file for detailed logging
```

## Why Use conda-forge?

conda-forge offers several advantages:

1. **Community-driven**: Packages are maintained by an active community
2. **Up-to-date**: Packages are typically more current than those in the default channel
3. **Broader selection**: More packages are available
4. **Consistent build**: Packages follow strict guidelines for compatibility
5. **Better dependency resolution**: Often resolves complex dependencies more effectively

## License

This project is licensed under the MIT License - see the LICENSE file for details.
