# Developer Setup Guide for GitHub Actions Local Testing on Windows

This guide will help you set up your local environment for testing GitHub Actions workflows using VSCode, Windows 11, and Docker Desktop.

## Prerequisites

- Windows 11
- VSCode
- Docker Desktop
- Git for Windows

## Step 1: Install Docker Desktop

1. Download Docker Desktop for Windows from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
1. Run the installer and follow the prompts
1. Ensure WSL 2 is enabled when prompted
1. After installation, start Docker Desktop
1. Verify Docker is running by opening a terminal and running:
   ```
   docker --version
   ```

## Step 2: Install Required Tools in VSCode

1. Open VSCode

1. Install the following extensions:

   - Docker (ms-azuretools.vscode-docker)
   - GitHub Actions (github.vscode-github-actions)
   - YAML (redhat.vscode-yaml)
   - Remote - WSL (ms-vscode-remote.remote-wsl) (optional, for WSL users)

1. Open the terminal in VSCode (Terminal > New Terminal)

1. Install actionlint:

   ```powershell
   # Using Chocolatey (install Chocolatey first if you don't have it)
   choco install actionlint

   # Or using Scoop
   scoop install actionlint

   # Or download the binary directly
   Invoke-WebRequest -Uri "https://github.com/rhysd/actionlint/releases/latest/download/actionlint_windows_amd64.zip" -OutFile "actionlint.zip"
   Expand-Archive -Path "actionlint.zip" -DestinationPath "$env:USERPROFILE\actionlint"
   $env:PATH += ";$env:USERPROFILE\actionlint"
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
   ```

1. Install act:

   ```powershell
   # Using Chocolatey
   choco install act-cli

   # Or using Scoop
   scoop install act

   # Or download the binary directly
   Invoke-WebRequest -Uri "https://github.com/nektos/act/releases/latest/download/act_Windows_x86_64.zip" -OutFile "act.zip"
   Expand-Archive -Path "act.zip" -DestinationPath "$env:USERPROFILE\act"
   $env:PATH += ";$env:USERPROFILE\act"
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
   ```

1. Install pre-commit:

   ```powershell
   pip install pre-commit
   ```

## Step 3: Configure Docker Desktop

1. Open Docker Desktop
1. Go to Settings > Resources
1. Allocate sufficient resources:
   - CPUs: at least 2
   - Memory: at least 4 GB
   - Swap: at least 1 GB
   - Disk image size: at least 60 GB
1. Go to Settings > Docker Engine
1. Add the following configuration to improve performance:
   ```json
   {
     "experimental": true,
     "features": {
       "buildkit": true
     },
     "builder": {
       "gc": {
         "enabled": true,
         "defaultKeepStorage": "20GB"
       }
     }
   }
   ```
1. Click "Apply & Restart"

## Step 4: Clone the Repository and Set Up Local Testing

1. Clone the repository in VSCode:

   ```powershell
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

1. Install pre-commit hooks:

   ```powershell
   pre-commit install
   ```

1. Create the local testing directory structure:

   ```powershell
   mkdir -p .github/local-testing/events
   ```

1. Create the `.actrc` file in the repository root:

   ```
   -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
   -P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04
   -P ubuntu-20.04=ghcr.io/catthehacker/ubuntu:act-20.04
   ```

1. Create the test scripts:

   - Create `.github/local-testing/test-workflow.sh`
   - Create `.github/local-testing/test-python-versions.sh`
   - Make them executable (not needed on Windows, but good for cross-platform compatibility)

## Step 5: Windows-Specific Configuration

### Using Git Bash

For the best experience with shell scripts, use Git Bash:

1. In VSCode, open settings (File > Preferences > Settings)
1. Search for "terminal.integrated.defaultProfile.windows"
1. Set it to "Git Bash"
1. Restart VSCode

### Path Conversion

Windows uses backslashes, but our scripts expect forward slashes. When running commands, use forward slashes:

```bash
# Correct
./github/local-testing/test-workflow.sh .github/workflows/ci.yml

# Incorrect
.\github\local-testing\test-workflow.sh .github\workflows\ci.yml
```

### Running Shell Scripts on Windows

To run the shell scripts on Windows:

1. Using Git Bash in VSCode terminal:

   ```bash
   bash .github/local-testing/test-workflow.sh .github/workflows/ci.yml
   ```

1. Or create PowerShell wrapper scripts:

   ```powershell
   # test-workflow.ps1
   param(
       [Parameter(Mandatory=$true)][string]$WorkflowFile,
       [string]$EventType = "push",
       [string]$MatrixOverride = ""
   )

   bash .github/local-testing/test-workflow.sh $WorkflowFile $EventType $MatrixOverride
   ```

## Troubleshooting

### Docker Connection Issues

If you encounter Docker connection issues:

1. Ensure Docker Desktop is running
1. Restart Docker Desktop
1. Check Docker service in Task Manager > Services
1. Run `docker ps` to verify connectivity

### WSL 2 Issues

If you encounter WSL 2 issues:

1. Open PowerShell as Administrator
1. Run `wsl --update`
1. Run `wsl --shutdown`
1. Restart Docker Desktop

### Act Permission Issues

If you encounter permission issues with act:

1. Run Docker Desktop as Administrator
1. Try running act with `--privileged` flag
1. Check Windows Defender settings for Docker

### Large Image Downloads

The first time you run act, it will download Docker images which can be large:

1. Ensure you have a good internet connection
1. Be patient during the first run
1. Consider running during off-hours if on a metered connection

## Testing Your Setup

To verify your setup is working correctly:

1. Run a simple workflow test:

   ```bash
   bash .github/local-testing/test-workflow.sh .github/workflows/ci.yml
   ```

1. Test with a specific Python version:

   ```bash
   bash .github/local-testing/test-workflow.sh .github/workflows/ci.yml push python-version=3.11
   ```

1. Test both Python versions:

   ```bash
   bash .github/local-testing/test-python-versions.sh .github/workflows/ci.yml
   ```

If these commands run without errors, your setup is working correctly!
