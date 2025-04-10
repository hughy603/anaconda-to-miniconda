# VSCode Configuration for conda-forge-converter

This directory contains VSCode configuration files to help you quickly set up your development environment for the conda-forge-converter project.

## Files Overview

- **launch.json**: Debug configurations for various scenarios
- **settings.json**: Editor and Python extension settings
- **tasks.json**: Common development tasks
- **extensions.json**: Recommended VSCode extensions

## Debug Configurations

The `launch.json` file includes several debug configurations:

1. **Debug CLI**: Run the CLI with basic arguments
1. **Debug Conda Integration**: Run with conda debugging enabled
1. **Debug Mamba Integration**: Run with mamba debugging enabled
1. **Debug Tests**: Run specific tests with debugging
1. **Debug All Tests**: Run all tests with debugging
1. **Debug Batch Conversion**: Debug batch conversion mode
1. **Debug Health Check**: Debug the health check command

To use these configurations:

1. Open the Debug panel in VSCode (Ctrl+Shift+D or Cmd+Shift+D)
1. Select a configuration from the dropdown
1. Click the green play button or press F5

## Tasks

The `tasks.json` file includes common development tasks:

- **Install Development Dependencies**: Set up your development environment
- **Run Tests**: Run the test suite
- **Run Tests with Coverage**: Run tests with coverage reporting
- **Lint with Ruff**: Check code quality
- **Format with Ruff**: Format code
- **Type Check with Pyright**: Check type annotations
- **Lock Dependencies**: Update the requirements.lock file
- **Install Pre-commit Hooks**: Set up pre-commit hooks
- **Run Pre-commit Hooks**: Run all pre-commit hooks
- **Build Documentation**: Build the documentation
- **Serve Documentation**: Serve the documentation locally
- **Check Conda Environment**: Display conda information
- **List Conda Environments**: List available conda environments
- **Check Mamba Installation**: Display mamba information

To run a task:

1. Press Ctrl+Shift+P (or Cmd+Shift+P on macOS)
1. Type "Tasks: Run Task"
1. Select the task you want to run

## Debugging Conda/Mamba Integration

When debugging integration with conda/mamba:

1. Use the "Debug Conda Integration" or "Debug Mamba Integration" launch configurations
1. These configurations set environment variables (`CONDA_DEBUG=1` or `MAMBA_DEBUG=1`) to enable verbose output
1. Set breakpoints in the following files:
   - `src/conda_forge_converter/core.py`: For environment creation and package installation
   - `src/conda_forge_converter/utils.py`: For command execution
   - `src/conda_forge_converter/cli.py`: For command-line interface

## Recommended Extensions

The `extensions.json` file recommends several VSCode extensions that enhance your development experience:

- Python language support
- Ruff for linting and formatting
- TOML and YAML support
- Markdown tools
- Git integration
- GitHub Actions support

VSCode will automatically suggest installing these extensions when you open the project.

## Customization

Feel free to customize these configurations to suit your workflow:

- Modify `launch.json` to add new debug configurations
- Update `settings.json` to change editor or Python settings
- Add new tasks to `tasks.json`
- Add or remove extensions in `extensions.json`
