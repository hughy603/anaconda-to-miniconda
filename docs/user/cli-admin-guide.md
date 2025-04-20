# CLI Guide for System Administrators

This guide provides detailed information for system administrators using the conda-forge-converter CLI tool in multi-user environments.

## Installation

### System-wide Installation

```bash
# Install for all users
sudo pip install conda-forge-converter

# Verify installation
conda-forge-converter --version
```

### Installation in Isolated Environment

```bash
# Create a dedicated environment
conda create -n converter-admin -c conda-forge python=3.10
conda activate converter-admin

# Install the package
pip install conda-forge-converter
```

## Common Administrative Tasks

### Converting Environments for Multiple Users

As a system administrator, you may need to convert environments owned by different users. The conda-forge-converter tool supports running as root to handle this scenario.

```bash
# Convert an environment owned by another user
sudo conda-forge-converter -s /home/user1/anaconda3/envs/data_science -t data_science_forge

# Batch convert all environments matching a pattern
sudo conda-forge-converter --batch --pattern 'data*'
```

### Ownership Preservation

When running as root, the converter automatically preserves the original ownership of environments:

```bash
# Environment 'data_science' owned by user 'analyst' will remain owned by 'analyst'
sudo conda-forge-converter -s data_science -t data_science_forge
```

To disable this behavior:

```bash
# Create environments owned by root
sudo conda-forge-converter -s data_science -t data_science_forge --no-preserve-ownership
```

### Scheduled Conversions

For scheduled maintenance, you can create a script and run it via cron:

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

## Environment Variables

The conda-forge-converter respects the following environment variables:

| Variable | Description | Default |
| ---------------------------------- | ------------------------------------------- | -------------------------------- |
| `CONDA_FORGE_CONVERTER_CACHE_DIR` | Directory for caching package metadata | `~/.cache/conda-forge-converter` |
| `CONDA_FORGE_CONVERTER_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `CONDA_FORGE_CONVERTER_TIMEOUT` | Timeout for network operations (seconds) | `60` |
| `CONDA_FORGE_CONVERTER_BATCH_SIZE` | Number of packages to install in a batch | `20` |

Example usage:

```bash
# Increase batch size for faster installation
export CONDA_FORGE_CONVERTER_BATCH_SIZE=50

# Set custom cache directory
export CONDA_FORGE_CONVERTER_CACHE_DIR=/var/cache/conda-forge-converter

# Run with these settings
conda-forge-converter -s myenv -t myenv_forge
```

## Security Considerations

### Running as Root

When running as root:

- The tool can modify file ownership and permissions
- It has access to all conda environments on the system
- It can create and modify files in system directories

Best practices:

- Use a dedicated service account instead of root when possible
- Ensure proper filesystem permissions are configured
- Be cautious when converting environments in system directories
- Regularly audit logs for unexpected behavior

### File Permissions

The converter maintains the original file permissions when preserving ownership:

```bash
# Check permissions before conversion
ls -la /home/user1/anaconda3/envs/data_science

# Convert the environment
sudo conda-forge-converter -s /home/user1/anaconda3/envs/data_science -t data_science_forge

# Verify permissions are preserved
ls -la /home/user1/anaconda3/envs/data_science_forge
```

### SELinux Considerations

On systems with SELinux enabled, you may encounter permission issues even when running as root:

```bash
# Temporarily set SELinux to permissive mode
sudo setenforce 0

# Run the conversion
sudo conda-forge-converter -s myenv -t myenv_forge

# Restore SELinux to enforcing mode
sudo setenforce 1
```

For a permanent solution, create a custom SELinux policy:

```bash
# Create a policy for conda-forge-converter
sudo ausearch -c 'conda-forge-conv' --raw | audit2allow -M conda_forge_converter
sudo semodule -i conda_forge_converter.pp
```

## Troubleshooting

### Permission Issues

If you encounter permission issues even when running as root:

1. Check SELinux status: `getenforce`
1. Check filesystem mount options: `mount | grep <path>`
1. Check for immutable attributes: `lsattr <path>`

### Ownership Not Preserved

If ownership is not being preserved as expected:

1. Verify you're running as root: `id -u` should return 0
1. Make sure you haven't used the `--no-preserve-ownership` flag
1. Check if the source environment exists and is accessible
1. Ensure the target environment name doesn't already exist

### Log Files

The converter logs detailed information to help diagnose issues:

```bash
# Run with verbose logging
conda-forge-converter -s myenv -t myenv_forge --verbose

# Check system logs for errors
sudo journalctl | grep conda-forge-converter
```

## Advanced Usage

### Custom Configuration

Create a configuration file at `/etc/conda-forge-converter/config.yaml`:

```yaml
# /etc/conda-forge-converter/config.yaml
cache_dir: /var/cache/conda-forge-converter
batch_size: 50
timeout: 120
log_level: INFO
preserve_ownership: true
```

### Integration with Configuration Management

For Ansible:

```yaml
- name: Install conda-forge-converter
  pip:
    name: conda-forge-converter
    state: present
  become: yes

- name: Convert environment
  command: conda-forge-converter -s data_science -t data_science_forge
  become: yes
  become_user: analyst
```

For Puppet:

```puppet
package { 'conda-forge-converter':
  ensure   => present,
  provider => 'pip3',
}

exec { 'convert_environment':
  command => '/usr/local/bin/conda-forge-converter -s data_science -t data_science_forge',
  user    => 'analyst',
  path    => ['/usr/local/bin', '/usr/bin', '/bin'],
  require => Package['conda-forge-converter'],
}
```

## Command Reference

### Basic Commands

| Command | Description |
| ------------------------------------------------- | ---------------------------------------------- |
| `conda-forge-converter --help` | Show help message |
| `conda-forge-converter --version` | Show version information |
| `conda-forge-converter -s SOURCE -t TARGET` | Convert a single environment |
| `conda-forge-converter --batch` | Convert all environments |
| `conda-forge-converter --batch --pattern PATTERN` | Convert environments matching pattern |
| `conda-forge-converter --dry-run` | Show what would be done without making changes |
| `conda-forge-converter --verbose` | Show detailed output |

### Advanced Options

| Option | Description |
| -------------------------- | ---------------------------------------------------- |
| `--no-preserve-ownership` | Don't preserve original environment ownership |
| `--python-version VERSION` | Specify Python version for the new environment |
| `--use-fast-solver` | Use libmamba solver for faster dependency resolution |
| `--batch-size SIZE` | Number of packages to install in a batch |
| `--no-backup` | Skip creating backup of the original environment |
| `--skip-validation` | Skip validation of the converted environment |
