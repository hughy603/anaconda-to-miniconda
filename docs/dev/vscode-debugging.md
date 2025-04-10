# VSCode Debugging Guide

This guide explains how to use VSCode for debugging the conda-forge-converter tool, with a focus on debugging integration with conda/mamba.

## Setup

The project includes a pre-configured VSCode environment to help you get started quickly. The configuration files are located in the `.vscode` directory.

### Automatic Setup

Run the setup script to automatically configure VSCode:

```bash
./scripts/setup_vscode.py
```

This script will:

1. Create the `.vscode` directory if it doesn't exist
1. Generate configuration files (launch.json, settings.json, tasks.json, extensions.json)
1. Detect your Python interpreter and conda/mamba installations
1. Customize the configuration based on your environment

### Manual Setup

If you prefer to set up VSCode manually, you can copy the configuration files from the `.vscode` directory to your project.

## Debugging Conda/Mamba Integration

The conda-forge-converter tool interacts with conda and mamba to create and manage environments. Debugging these interactions can be challenging, but VSCode provides tools to make it easier.

### Debug Configurations

The `.vscode/launch.json` file includes several debug configurations specifically designed for debugging conda/mamba integration:

1. **Debug Conda Integration**: Runs the CLI with conda debugging enabled
1. **Debug Mamba Integration**: Runs the CLI with mamba debugging enabled

These configurations set environment variables (`CONDA_DEBUG=1` or `MAMBA_DEBUG=1`) to enable verbose output from conda/mamba.

### Setting Breakpoints

To debug conda/mamba integration effectively, set breakpoints in the following files:

1. **src/conda_forge_converter/core.py**:

   - `create_conda_forge_environment`: For environment creation
   - `_install_conda_packages_in_batches`: For package installation
   - `_install_pip_packages_in_batches`: For pip package installation

1. **src/conda_forge_converter/utils.py**:

   - `run_command`: For command execution
   - `is_command_output_str`: For command output processing

1. **src/conda_forge_converter/cli.py**:

   - `main`: For command-line interface entry point

### Debugging Process

Follow these steps to debug conda/mamba integration:

1. Open the Debug panel in VSCode (Ctrl+Shift+D or Cmd+Shift+D)
1. Select "Debug Conda Integration" or "Debug Mamba Integration" from the dropdown
1. Set breakpoints in the relevant files
1. Click the green play button or press F5 to start debugging
1. When the breakpoint is hit, you can:
   - Inspect variables
   - Step through code
   - View the call stack
   - Evaluate expressions in the Debug Console

### Examining Command Output

When debugging conda/mamba integration, it's important to examine the output of conda/mamba commands. You can do this by:

1. Setting a breakpoint after the `run_command` function call
1. Inspecting the `output` variable in the Variables panel
1. Using the Debug Console to evaluate expressions

### Common Integration Issues

Here are some common issues you might encounter when debugging conda/mamba integration:

1. **Command Execution Failures**:

   - Check the `run_command` function in utils.py
   - Examine the command being executed and its arguments
   - Look for error messages in the command output

1. **Package Resolution Issues**:

   - Debug the `_install_conda_packages_in_batches` function in core.py
   - Examine the package specifications being passed to conda/mamba
   - Look for solver errors in the command output

1. **Environment Creation Problems**:

   - Debug the `create_conda_forge_environment` function in core.py
   - Check the environment name and path
   - Verify that conda/mamba is available and working correctly

## Advanced Debugging Techniques

### Modifying Debug Configurations

You can modify the debug configurations in `.vscode/launch.json` to suit your specific needs. For example:

1. Change the command-line arguments to debug different scenarios
1. Add additional environment variables for more detailed debugging
1. Configure the debugger to stop on specific exceptions

### Using the Debug Console

The Debug Console allows you to evaluate expressions while debugging. This can be useful for:

1. Inspecting complex data structures
1. Testing code snippets
1. Modifying variables during debugging

### Conditional Breakpoints

You can set conditional breakpoints to stop execution only when certain conditions are met:

1. Right-click on a breakpoint
1. Select "Edit Breakpoint"
1. Enter a condition (e.g., `env_name == "myenv"`)

This is particularly useful when debugging batch operations that process multiple environments.

## Troubleshooting

### Debugger Not Stopping at Breakpoints

If the debugger is not stopping at your breakpoints:

1. Verify that the breakpoints are set in the correct files
1. Check that the files being executed match the files where you set breakpoints
1. Ensure that the Python interpreter in VSCode matches the one being used to run the code

### Conda/Mamba Not Found

If conda or mamba is not found during debugging:

1. Verify that conda/mamba is installed and available in your PATH
1. Check the environment variables in the debug configuration
1. Try running the commands manually in the terminal to confirm they work

### Other Issues

For other debugging issues:

1. Check the VSCode output panel for error messages
1. Verify that the Python extension is installed and configured correctly
1. Restart VSCode if necessary
