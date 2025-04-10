# CLI Documentation Guide

This guide provides standards and best practices for documenting command-line interface (CLI) features in the Conda-Forge Converter project. Following these guidelines ensures consistent, clear, and comprehensive CLI documentation.

## General Principles

- **Consistency**: Use consistent terminology and formatting across all CLI documentation
- **Completeness**: Document all commands, options, and arguments
- **Examples**: Include practical examples for all commands
- **Context**: Explain when and why to use each command
- **Audience**: Consider both novice and experienced users

## Command Documentation Structure

Each CLI command should be documented using the following structure:

1. **Command Name and Synopsis**

   - Command name
   - Brief one-line description
   - Basic syntax

1. **Description**

   - Detailed explanation of what the command does
   - When to use it
   - How it relates to other commands

1. **Options and Arguments**

   - Complete list of all options and arguments
   - Description of each option/argument
   - Default values
   - Required vs. optional

1. **Examples**

   - Basic usage example
   - Examples with different options
   - Real-world use case examples

1. **Output**

   - Description of command output
   - Example output
   - How to interpret the output

1. **Related Commands**

   - Links to related commands
   - Common command combinations

## Formatting Guidelines

### Command Syntax

Use the following format for command syntax:

```
command [required_arg] [optional_arg] [--required-option VALUE] [--optional-option[=VALUE]]
```

- Use square brackets `[]` for optional elements
- Use angle brackets `<>` for placeholder values
- Use all caps for placeholder values that should be replaced
- Use ellipsis `...` for repeatable elements

### Options

Document options in a table format:

| Option      | Description             | Default    | Required |
| ----------- | ----------------------- | ---------- | -------- |
| `--option1` | Description of option 1 | `default1` | Yes/No   |
| `--option2` | Description of option 2 | `default2` | Yes/No   |

### Examples

Format examples as follows:

```bash
# Example description
command arg --option value
```

Include the expected output when helpful:

```
Expected output line 1
Expected output line 2
```

## CLI Documentation for Different User Types

### For Package Developers

- Focus on development-related commands
- Include examples relevant to package development
- Explain integration with development workflows

### For System Administrators

- Focus on installation, configuration, and maintenance
- Include examples for multi-user environments
- Document security considerations
- Explain integration with system tools

### For End Users

- Focus on basic usage commands
- Include step-by-step examples
- Avoid technical jargon
- Provide troubleshooting guidance

## Best Practices

### Do's

- ✅ Document all commands, options, and arguments
- ✅ Include examples for common use cases
- ✅ Explain when to use each command
- ✅ Provide context for command options
- ✅ Use consistent terminology
- ✅ Include error messages and troubleshooting
- ✅ Update documentation when CLI changes

### Don'ts

- ❌ Assume prior knowledge
- ❌ Use inconsistent formatting
- ❌ Omit important options
- ❌ Provide examples without explanation
- ❌ Use technical jargon without explanation
- ❌ Leave outdated documentation

## Example CLI Documentation

Here's an example of well-documented CLI command:

### `conda-forge-converter`

Convert Anaconda environments to conda-forge environments.

#### Synopsis

```
conda-forge-converter [-s SOURCE] [-t TARGET] [--python-version VERSION] [--dry-run] [--verbose]
```

#### Description

The `conda-forge-converter` command converts an existing Anaconda environment to use conda-forge packages while preserving package versions. It creates a new environment with the same packages but sourced from the conda-forge channel.

#### Options

| Option                    | Description                                                        | Default        | Required |
| ------------------------- | ------------------------------------------------------------------ | -------------- | -------- |
| `-s, --source`            | Source environment name or path                                    | -              | Yes      |
| `-t, --target`            | Target environment name                                            | -              | Yes      |
| `--python-version`        | Python version for the new environment                             | Same as source | No       |
| `--dry-run`               | Show what would be done without making changes                     | `False`        | No       |
| `--verbose`               | Show detailed output                                               | `False`        | No       |
| `--batch`                 | Convert multiple environments                                      | `False`        | No       |
| `--pattern`               | Pattern to match environment names when using --batch              | `*`            | No       |
| `--no-preserve-ownership` | Don't preserve original environment ownership when running as root | `False`        | No       |

#### Examples

Basic usage:

```bash
# Convert 'data_science' environment to 'data_science_forge'
conda-forge-converter -s data_science -t data_science_forge
```

With specific Python version:

```bash
# Convert environment and use Python 3.10
conda-forge-converter -s data_science -t data_science_forge --python-version 3.10
```

Batch conversion:

```bash
# Convert all environments matching the pattern 'data*'
conda-forge-converter --batch --pattern 'data*'
```

Running as root:

```bash
# Convert environment owned by another user while preserving ownership
sudo conda-forge-converter -s /home/user1/anaconda3/envs/data_science -t data_science_forge
```

#### Output

Successful conversion:

```
Environment 'data_science' successfully converted to 'data_science_forge'
All packages installed from conda-forge
```

#### Related Commands

- `conda-forge-converter --help` - Show help message
- `conda-forge-converter --version` - Show version information
