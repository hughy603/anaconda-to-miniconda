#!/usr/bin/env python3
"""
Setup script for VSCode configuration.

This script sets up VSCode configuration files for the conda-forge-converter project.
It creates the .vscode directory and configuration files if they don't exist.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Define colors for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
ENDC = "\033[0m"
BOLD = "\033[1m"


def print_colored(message: str, color: str = BLUE, bold: bool = False) -> None:
    """Print a colored message to the terminal."""
    if bold:
        print(f"{BOLD}{color}{message}{ENDC}")
    else:
        print(f"{color}{message}{ENDC}")


def get_project_root() -> Path:
    """Get the project root directory."""
    # Assuming this script is in the scripts directory
    return Path(__file__).parent.parent.absolute()


def check_python_interpreter() -> str | None:
    """Check for Python interpreter."""
    # Check for virtual environment
    venv_path = get_project_root() / ".venv" / "bin" / "python"
    if venv_path.exists():
        return str(venv_path)

    # Check for conda environment
    try:
        result = subprocess.run(
            ["conda", "info", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        conda_info = json.loads(result.stdout)
        active_env = conda_info.get("active_env_path")
        if active_env:
            python_path = os.path.join(active_env, "bin", "python")
            if os.path.exists(python_path):
                return python_path
    except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
        pass

    # Return system Python as fallback
    return sys.executable


def check_conda_installation() -> dict[str, bool]:
    """Check for conda and mamba installations."""
    result = {"conda": False, "mamba": False}

    # Check for conda
    try:
        subprocess.run(
            ["conda", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        result["conda"] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Check for mamba
    try:
        subprocess.run(
            ["mamba", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        result["mamba"] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return result


def create_vscode_directory() -> Path:
    """Create .vscode directory if it doesn't exist."""
    vscode_dir = get_project_root() / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    return vscode_dir


def create_launch_json(vscode_dir: Path) -> None:
    """Create launch.json file."""
    launch_json_path = vscode_dir / "launch.json"

    # Skip if file already exists
    if launch_json_path.exists():
        print_colored("launch.json already exists. Skipping.", YELLOW)
        return

    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Debug CLI",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/src/conda_forge_converter/cli.py",
                "args": ["--source-env", "myenv", "--target-env", "myenv_forge", "--verbose"],
                "console": "integratedTerminal",
                "justMyCode": False,
                "env": {"PYTHONPATH": "${workspaceFolder}"},
            },
            {
                "name": "Debug Conda Integration",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/src/conda_forge_converter/cli.py",
                "args": ["--source-env", "myenv", "--target-env", "myenv_forge", "--verbose"],
                "console": "integratedTerminal",
                "justMyCode": False,
                "env": {"PYTHONPATH": "${workspaceFolder}", "CONDA_DEBUG": "1"},
            },
            {
                "name": "Debug Mamba Integration",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/src/conda_forge_converter/cli.py",
                "args": ["--source-env", "myenv", "--target-env", "myenv_forge", "--verbose"],
                "console": "integratedTerminal",
                "justMyCode": False,
                "env": {"PYTHONPATH": "${workspaceFolder}", "MAMBA_DEBUG": "1"},
            },
            {
                "name": "Debug Tests",
                "type": "python",
                "request": "launch",
                "module": "pytest",
                "args": ["tests/test_core.py", "-v"],
                "console": "integratedTerminal",
                "justMyCode": False,
            },
            {
                "name": "Debug All Tests",
                "type": "python",
                "request": "launch",
                "module": "pytest",
                "args": ["-v"],
                "console": "integratedTerminal",
                "justMyCode": False,
            },
            {
                "name": "Debug Batch Conversion",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/src/conda_forge_converter/cli.py",
                "args": ["--batch", "--pattern", "data*", "--verbose"],
                "console": "integratedTerminal",
                "justMyCode": False,
                "env": {"PYTHONPATH": "${workspaceFolder}"},
            },
            {
                "name": "Debug Health Check",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/src/conda_forge_converter/cli.py",
                "args": ["health", "myenv", "--verbose"],
                "console": "integratedTerminal",
                "justMyCode": False,
                "env": {"PYTHONPATH": "${workspaceFolder}"},
            },
        ],
    }

    with launch_json_path.open("w") as f:
        json.dump(launch_config, f, indent=4)

    print_colored("Created launch.json", GREEN)


def create_settings_json(vscode_dir: Path, python_path: str | None = None) -> None:
    """Create settings.json file."""
    settings_json_path = vscode_dir / "settings.json"

    # Skip if file already exists
    if settings_json_path.exists():
        print_colored("settings.json already exists. Skipping.", YELLOW)
        return

    # Use detected Python path or default to workspace virtual environment
    python_interpreter = python_path or "${workspaceFolder}/.venv/bin/python"

    settings_config = {
        "python.defaultInterpreterPath": python_interpreter,
        "python.analysis.typeCheckingMode": "basic",
        "python.linting.enabled": True,
        "python.linting.lintOnSave": True,
        "python.formatting.provider": "none",
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {"source.organizeImports": True, "source.fixAll": True},
        "[python]": {
            "editor.defaultFormatter": "charliermarsh.ruff",
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {"source.organizeImports": True, "source.fixAll": True},
        },
        "terminal.integrated.env.linux": {"PYTHONPATH": "${workspaceFolder}"},
        "terminal.integrated.env.osx": {"PYTHONPATH": "${workspaceFolder}"},
        "terminal.integrated.env.windows": {"PYTHONPATH": "${workspaceFolder}"},
        "python.testing.pytestEnabled": True,
        "python.testing.unittestEnabled": False,
        "python.testing.nosetestsEnabled": False,
        "python.testing.pytestArgs": ["tests"],
        "python.envFile": "${workspaceFolder}/.env",
        "python.analysis.extraPaths": ["${workspaceFolder}/src"],
        "python.analysis.diagnosticMode": "workspace",
        "python.analysis.autoImportCompletions": True,
        "python.analysis.indexing": True,
        "python.analysis.packageIndexDepths": [{"name": "conda_forge_converter", "depth": 5}],
        "files.exclude": {
            "**/__pycache__": True,
            "**/.pytest_cache": True,
            "**/.mypy_cache": True,
            "**/.ruff_cache": True,
        },
        "search.exclude": {
            "**/__pycache__": True,
            "**/.pytest_cache": True,
            "**/.mypy_cache": True,
            "**/.ruff_cache": True,
        },
    }

    with settings_json_path.open("w") as f:
        json.dump(settings_config, f, indent=4)

    print_colored("Created settings.json", GREEN)


def create_tasks_json(vscode_dir: Path, conda_info: dict[str, bool]) -> None:
    """Create tasks.json file."""
    tasks_json_path = vscode_dir / "tasks.json"

    # Skip if file already exists
    if tasks_json_path.exists():
        print_colored("tasks.json already exists. Skipping.", YELLOW)
        return

    tasks = [
        {
            "label": "Install Development Dependencies",
            "type": "shell",
            "command": 'uv pip install -e ".[dev,test]"',
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
            "group": {"kind": "build", "isDefault": True},
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "pytest",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
            "group": {"kind": "test", "isDefault": True},
        },
        {
            "label": "Run Tests with Coverage",
            "type": "shell",
            "command": "pytest --cov=conda_forge_converter tests/",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
        {
            "label": "Lint with Ruff",
            "type": "shell",
            "command": "ruff check .",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
        {
            "label": "Format with Ruff",
            "type": "shell",
            "command": "ruff format .",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
        {
            "label": "Type Check with Pyright",
            "type": "shell",
            "command": "pyright",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
        {
            "label": "Lock Dependencies",
            "type": "shell",
            "command": "uv pip compile pyproject.toml --output-file=requirements.lock --extra=dev --extra=test",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
        {
            "label": "Install Pre-commit Hooks",
            "type": "shell",
            "command": "pre-commit install",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
        {
            "label": "Run Pre-commit Hooks",
            "type": "shell",
            "command": "pre-commit run --all-files",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
        {
            "label": "Build Documentation",
            "type": "shell",
            "command": "mkdocs build",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
        {
            "label": "Serve Documentation",
            "type": "shell",
            "command": "mkdocs serve",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new"},
        },
    ]

    # Add conda-specific tasks if conda is installed
    if conda_info["conda"]:
        tasks.extend(
            [
                {
                    "label": "Check Conda Environment",
                    "type": "shell",
                    "command": "conda info",
                    "problemMatcher": [],
                    "presentation": {"reveal": "always", "panel": "new"},
                },
                {
                    "label": "List Conda Environments",
                    "type": "shell",
                    "command": "conda env list",
                    "problemMatcher": [],
                    "presentation": {"reveal": "always", "panel": "new"},
                },
            ]
        )

    # Add mamba-specific tasks if mamba is installed
    if conda_info["mamba"]:
        tasks.append(
            {
                "label": "Check Mamba Installation",
                "type": "shell",
                "command": "mamba info",
                "problemMatcher": [],
                "presentation": {"reveal": "always", "panel": "new"},
            }
        )

    tasks_config = {"version": "2.0.0", "tasks": tasks}

    with tasks_json_path.open("w") as f:
        json.dump(tasks_config, f, indent=4)

    print_colored("Created tasks.json", GREEN)


def create_extensions_json(vscode_dir: Path) -> None:
    """Create extensions.json file."""
    extensions_json_path = vscode_dir / "extensions.json"

    # Skip if file already exists
    if extensions_json_path.exists():
        print_colored("extensions.json already exists. Skipping.", YELLOW)
        return

    extensions_config = {
        "recommendations": [
            "ms-python.python",
            "ms-python.vscode-pylance",
            "charliermarsh.ruff",
            "matangover.mypy",
            "njpwerner.autodocstring",
            "tamasfe.even-better-toml",
            "redhat.vscode-yaml",
            "ms-python.debugpy",
            "ms-python.black-formatter",
            "ms-toolsai.jupyter",
            "bierner.markdown-mermaid",
            "davidanson.vscode-markdownlint",
            "yzhang.markdown-all-in-one",
            "streetsidesoftware.code-spell-checker",
            "eamodio.gitlens",
            "github.vscode-github-actions",
        ],
        "unwantedRecommendations": ["ms-python.flake8", "ms-python.isort"],
    }

    with extensions_json_path.open("w") as f:
        json.dump(extensions_config, f, indent=4)

    print_colored("Created extensions.json", GREEN)


def create_readme(vscode_dir: Path) -> None:
    """Create README.md file in the .vscode directory."""
    readme_path = vscode_dir / "README.md"

    # Skip if file already exists
    if readme_path.exists():
        print_colored("README.md already exists. Skipping.", YELLOW)
        return

    readme_content = """# VSCode Configuration for conda-forge-converter

This directory contains VSCode configuration files to help you quickly set up your development environment for the conda-forge-converter project.

## Files Overview

- **launch.json**: Debug configurations for various scenarios
- **settings.json**: Editor and Python extension settings
- **tasks.json**: Common development tasks
- **extensions.json**: Recommended VSCode extensions

## Debug Configurations

The `launch.json` file includes several debug configurations:

1. **Debug CLI**: Run the CLI with basic arguments
2. **Debug Conda Integration**: Run with conda debugging enabled
3. **Debug Mamba Integration**: Run with mamba debugging enabled
4. **Debug Tests**: Run specific tests with debugging
5. **Debug All Tests**: Run all tests with debugging
6. **Debug Batch Conversion**: Debug batch conversion mode
7. **Debug Health Check**: Debug the health check command

To use these configurations:
1. Open the Debug panel in VSCode (Ctrl+Shift+D or Cmd+Shift+D)
2. Select a configuration from the dropdown
3. Click the green play button or press F5

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
2. Type "Tasks: Run Task"
3. Select the task you want to run

## Debugging Conda/Mamba Integration

When debugging integration with conda/mamba:

1. Use the "Debug Conda Integration" or "Debug Mamba Integration" launch configurations
2. These configurations set environment variables (`CONDA_DEBUG=1` or `MAMBA_DEBUG=1`) to enable verbose output
3. Set breakpoints in the following files:
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
"""

    with readme_path.open("w") as f:
        f.write(readme_content)

    print_colored("Created README.md", GREEN)


def configure_git_settings() -> bool | None:
    """Configure Git settings for the project.

    Returns:
        Optional[bool]: True if successful, False if failed, None if git not found
    """
    print_colored("Configuring Git settings...", BLUE)

    # Check if git is installed
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        print_colored("Git not found. Skipping Git configuration.", YELLOW)
        return None

    # Configure git pull.rebase to false for this repository
    try:
        subprocess.run(
            ["git", "config", "pull.rebase", "false"],
            capture_output=True,
            text=True,
            check=True,
        )
        print_colored("Git pull.rebase set to false for this repository.", GREEN)
        return True
    except subprocess.SubprocessError:
        print_colored("Failed to configure Git settings.", RED)
        return False


def main() -> None:
    """Main function."""
    print_colored("Setting up VSCode configuration for conda-forge-converter...", BLUE, bold=True)

    # Check for Python interpreter
    print_colored("Checking for Python interpreter...", BLUE)
    python_path = check_python_interpreter()
    if python_path:
        print_colored(f"Found Python interpreter: {python_path}", GREEN)
    else:
        print_colored("Could not find Python interpreter. Using default.", YELLOW)

    # Check for conda/mamba
    print_colored("Checking for conda/mamba...", BLUE)
    conda_info = check_conda_installation()
    if conda_info["conda"]:
        print_colored("Found conda installation.", GREEN)
    else:
        print_colored("conda not found.", YELLOW)

    if conda_info["mamba"]:
        print_colored("Found mamba installation.", GREEN)
    else:
        print_colored("mamba not found.", YELLOW)

    # Create .vscode directory
    print_colored("Creating .vscode directory...", BLUE)
    vscode_dir = create_vscode_directory()

    # Create configuration files
    create_launch_json(vscode_dir)
    create_settings_json(vscode_dir, python_path)
    create_tasks_json(vscode_dir, conda_info)
    create_extensions_json(vscode_dir)
    create_readme(vscode_dir)

    # Configure Git settings
    git_result = configure_git_settings()

    print_colored("\nVSCode configuration setup complete!", GREEN, bold=True)
    print_colored("Open the project in VSCode to use the new configuration.", BLUE)
    print_colored("See .vscode/README.md for more information.", BLUE)

    if git_result is True:
        print_colored("\nGit configuration:", GREEN, bold=True)
        print_colored("- pull.rebase = false (prevents divergent branch issues)", GREEN)
    elif git_result is False:
        print_colored("\nWarning: Failed to configure Git settings.", YELLOW, bold=True)
        print_colored("Please manually run: git config pull.rebase false", YELLOW)


if __name__ == "__main__":
    main()
