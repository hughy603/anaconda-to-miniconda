# CLI Reference

Essential commands and options for the Conda-Forge Converter tool.

## Basic Commands

### Convert a Single Environment

```bash
conda-forge-converter -s SOURCE_ENV -t TARGET_ENV
```

### Convert Multiple Environments

```bash
conda-forge-converter --batch
```

### Check Environment Health

```bash
conda-forge-converter health ENV_NAME
```

### Get Help

```bash
conda-forge-converter --help
```

## Common Options

| Option                        | Description                                                    |
| ----------------------------- | -------------------------------------------------------------- |
| `-s, --source-env SOURCE_ENV` | Name of the source Anaconda environment                        |
| `-t, --target-env TARGET_ENV` | Name for the new conda-forge environment                       |
| `--python VERSION`            | Specify Python version for the new environment                 |
| `--dry-run`                   | Show what would be done without making changes                 |
| `--batch`                     | Convert multiple environments                                  |
| `--pattern PATTERN`           | Pattern for matching environment names (e.g., 'data\*')        |
| `--exclude EXCLUDE`           | Comma-separated list of environments to exclude                |
| `--target-suffix SUFFIX`      | Suffix to add to target environment names (default: "\_forge") |

## Examples

### Basic Conversion

```bash
conda-forge-converter -s myenv -t myenv_forge
```

### Batch Conversion with Pattern

```bash
conda-forge-converter --batch --pattern "data*" --exclude "test_env"
```

### Check Environment Health

```bash
conda-forge-converter health myenv
```
