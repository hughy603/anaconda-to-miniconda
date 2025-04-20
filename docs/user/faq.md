# Frequently Asked Questions (FAQ)

This document provides answers to frequently asked questions about the conda-forge-converter tool.

## General Questions

### What is conda-forge-converter?

conda-forge-converter is a tool that converts Anaconda environments to conda-forge environments while preserving package versions. It helps users migrate from Anaconda's default channels to the community-maintained conda-forge channel.

### Why should I convert to conda-forge?

There are several reasons to convert to conda-forge:

1. **Community-maintained**: conda-forge packages are maintained by a large community of contributors
1. **Up-to-date**: Packages are often updated more frequently
1. **Open source focus**: All packages in conda-forge are open source
1. **Wider selection**: conda-forge offers many packages not available in default channels
1. **Consistent build practices**: All packages follow consistent build practices

### Is conda-forge-converter official Anaconda software?

No, conda-forge-converter is not official Anaconda software. It's an independent tool designed to help users migrate between channels.

### Will converting break my environments?

The tool is designed to preserve functionality by maintaining the same package versions. However, there's always a small risk of incompatibilities. We recommend:

1. Using the `--dry-run` option first to see what changes would be made
1. Always keeping a backup of your original environment
1. Testing the converted environment thoroughly before relying on it

## Installation Questions

### How do I install conda-forge-converter?

You can install it using pip:

```bash
pip install conda-forge-converter
```

Or using conda:

```bash
conda install -c conda-forge conda-forge-converter
```

### What are the system requirements?

- Python 3.8 or higher
- conda 4.10.0 or higher
- Operating systems: Linux, macOS, or Windows

### Can I install it in an existing environment?

Yes, you can install it in any environment that meets the requirements. However, for isolation, we recommend installing it in a dedicated environment:

```bash
conda create -n converter -c conda-forge python=3.10 conda-forge-converter
conda activate converter
```

## Usage {#usage}

### Basic Usage

The basic command syntax is:

```bash
conda-forge-converter [OPTIONS] COMMAND [ARGS]...
```

Common options include:

- `--verbose`: Enable detailed output
- `--dry-run`: Show what would happen without making changes
- `--help`: Show help message and exit

For detailed command options, run:

```bash
conda-forge-converter --help
```

### Environment Variables

The tool respects the following environment variables:

- `CONDA_FORGE_CONVERTER_CACHE_DIR`: Cache directory location
- `CONDA_FORGE_CONVERTER_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CONDA_FORGE_CONVERTER_CONFIG`: Path to custom config file

## Common Workflows {#common-workflows}

### Converting a Single Environment

1. Create a backup of your environment:

   ```bash
   conda create --name myenv_backup --clone myenv
   ```

1. Convert the environment:

   ```bash
   conda-forge-converter -s myenv -t myenv_forge
   ```

1. Verify the conversion:

   ```bash
   conda-forge-converter verify myenv_forge
   ```

### Batch Converting Multiple Environments

1. List all environments:

   ```bash
   conda-forge-converter list
   ```

1. Convert matching environments:

   ```bash
   conda-forge-converter --batch --pattern "data*"
   ```

1. Verify all conversions:

   ```bash
   conda-forge-converter verify-all
   ```

### Automated Conversion Pipeline

For CI/CD pipelines:

```bash
#!/bin/bash
# Convert environments
conda-forge-converter --batch --non-interactive

# Verify conversions
conda-forge-converter verify-all --json > report.json

# Check for errors
if [ $(jq '.failed_envs | length' report.json) -gt 0 ]; then
    exit 1
fi
```

## System Administrator Questions

### Can I run conda-forge-converter as root?

Yes, you can run it as root to convert environments owned by different users. When running as root, the tool automatically preserves the original ownership of environments.

```bash
sudo conda-forge-converter -s /home/user/anaconda3/envs/myenv -t myenv_forge
```

### How do I disable ownership preservation?

Use the `--no-preserve-ownership` flag:

```bash
sudo conda-forge-converter -s myenv -t myenv_forge --no-preserve-ownership
```

### Can I automate conversions with cron?

Yes, you can create a script and run it via cron. Here's an example script:

```bash
#!/bin/bash
# /usr/local/bin/convert-environments.sh

LOG_FILE="/var/log/conda-forge-converter.log"
echo "Starting conversion at $(date)" >> $LOG_FILE

# Convert environments
/usr/local/bin/conda-forge-converter --batch --pattern 'prod*' >> $LOG_FILE 2>&1

echo "Conversion completed at $(date)" >> $LOG_FILE
```

Add to crontab:

```
# Run every Sunday at 2 AM
0 2 * * 0 /usr/local/bin/convert-environments.sh
```

## Troubleshooting Questions

### Why is the conversion taking so long?

Converting large environments can take time due to dependency resolution and package downloads. To speed up the process:

1. Use the `--use-fast-solver` option (enabled by default)
1. Increase the batch size: `--batch-size 50`
1. Ensure you have a fast internet connection
1. Consider converting during off-peak hours

### What do I do if a package isn't available in conda-forge?

If a package isn't available in conda-forge, you have several options:

1. Look for an alternative package that provides similar functionality
1. Install the missing package via pip after conversion
1. Contribute the package to conda-forge (see the [conda-forge documentation](https://conda-forge.org/docs/maintainer/adding_pkgs.html))
1. Keep using the Anaconda version of that specific package

### I'm getting permission errors even when running as root. What should I do?

This might be due to SELinux or filesystem restrictions:

1. Check SELinux status: `getenforce`
1. Temporarily set SELinux to permissive mode: `sudo setenforce 0`
1. Check filesystem mount options: `mount | grep <path>`
1. Check for immutable attributes: `lsattr <path>`

### How do I report bugs or request features?

You can report bugs or request features by opening an issue on our [GitHub repository](https://github.com/ricea/anaconda-to-miniconda2). Please use the provided issue templates and include as much information as possible.

## Performance Questions

### How can I make the conversion faster?

To improve conversion speed:

1. Use the fast solver (enabled by default): `--use-fast-solver`
1. Increase batch size: `--batch-size 50`
1. Set a larger cache directory: `export CONDA_FORGE_CONVERTER_CACHE_DIR=/path/with/space`
1. Convert smaller environments individually rather than very large ones
1. Ensure you have a fast and stable internet connection

### Will the converted environment use more disk space?

The converted environment will typically use a similar amount of disk space as the original. However, during the conversion process, both environments exist simultaneously, so you'll need enough disk space for both.

### Can I convert environments on a system with limited resources?

Yes, but you may need to adjust some settings:

1. Convert one environment at a time instead of using batch mode
1. Use a smaller batch size: `--batch-size 10`
1. Close other resource-intensive applications during conversion
1. Consider using a machine with more resources for very large environments
