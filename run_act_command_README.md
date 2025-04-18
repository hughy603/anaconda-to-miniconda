# Run Act Command

This script allows you to run GitHub Actions workflows locally using the `act` tool with real-time output. It's designed to help debug issues with workflow execution by showing the command output as it happens, rather than waiting for the entire process to complete.

## Features

- Run specific workflows with real-time output
- Target individual jobs within a workflow
- Set custom event types (push, pull_request, etc.)
- Configure timeouts to prevent hanging
- See the exact command being executed
- Debug mode with enhanced error information
- Step-by-step execution for detailed workflow debugging
- Workflow state inspection for troubleshooting

## Usage

```bash
python run_act_command.py <workflow_file> [options]
```

### Arguments

- `workflow_file`: The workflow file to run (required)

### Options

- `--job JOB`: The specific job to run within the workflow
- `--event EVENT`: The event type to trigger (default: push)
- `--timeout TIMEOUT`: Timeout in seconds (default: 300)
- `--verbose`: Show verbose output
- `--debug`: Enable debug mode with enhanced logging
- `--step-by-step`: Run workflow step by step, pausing after each step
- `--inspect`: Inspect the current state of workflow runs

### Examples

Run an entire workflow:

```bash
python run_act_command.py .github/workflows/ci.yml
```

Run a specific job:

```bash
python run_act_command.py .github/workflows/ci.yml --job build
```

Run with a pull_request event:

```bash
python run_act_command.py .github/workflows/ci.yml --event pull_request
```

Set a shorter timeout:

```bash
python run_act_command.py .github/workflows/ci.yml --timeout 60
```

Run in debug mode:

```bash
python run_act_command.py .github/workflows/ci.yml --debug
```

Run step by step:

```bash
python run_act_command.py .github/workflows/ci.yml --step-by-step
```

Inspect workflow state:

```bash
python run_act_command.py --inspect
```

## Advantages Over Using the Validator

1. **Real-time Output**: See the output as it happens, not after the process completes
1. **Direct Control**: Run specific jobs without going through the entire validation framework
1. **Easier Debugging**: Quickly identify where a job is hanging or failing
1. **Transparency**: See the exact command being executed
1. **Step-by-Step Execution**: Run workflows step by step for detailed debugging
1. **Enhanced GitHub Context**: More realistic simulation of GitHub environment variables
1. **State Inspection**: Examine workflow state for troubleshooting

## Requirements

- Python 3.6+
- The `act` tool must be installed and in your PATH
- Docker must be running (required by `act`)
- PyYAML package (`pip install pyyaml`) for step-by-step execution

## Debugging Features

### Debug Mode

Debug mode enables enhanced logging and provides more detailed error information:

```bash
python run_act_command.py .github/workflows/ci.yml --debug
```

This sets the `ACTIONS_STEP_DEBUG` and `ACTIONS_RUNNER_DEBUG` environment variables to enable GitHub Actions debug logging.

### Step-by-Step Execution

Step-by-step execution allows you to run a workflow one step at a time, pausing after each step:

```bash
python run_act_command.py .github/workflows/ci.yml --step-by-step
```

This is useful for:

- Identifying exactly which step is failing
- Examining the state between steps
- Testing individual steps in isolation

### Workflow State Inspection

The inspect feature allows you to examine the current state of workflow runs:

```bash
python run_act_command.py --inspect
```

This shows:

- Event files and their contents
- Workflow artifacts
- Log files
- Other state information

This is particularly useful for troubleshooting after a workflow has run.
