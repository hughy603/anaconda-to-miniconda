# Simple script to run act with custom images
# Usage: .\run-act.ps1 [workflow_file] [job_name] [event_type]

param(
    [string]$WorkflowFile = ".github/workflows/ci.yml",
    [string]$JobName = "",
    [string]$EventType = "push"
)

# Set environment variables
$env:ACT_LOCAL_TESTING = "true"
$env:PYTHON_VERSION = "3.11"
$env:UV_VERSION = "0.6.14"
$env:DOCS_VERSION = "main"

# Function to install act if not present
function Install-Act {
    if (-not (Get-Command act -ErrorAction SilentlyContinue)) {
        Write-Host "act not found. Installing..."

        # Check if Scoop is installed
        if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
            Write-Host "Installing Scoop package manager..."
            Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
            irm get.scoop.sh | iex
        }

        # Install act using Scoop
        scoop install act
    }
}

# Error checking
if (-not (Test-Path $WorkflowFile)) {
    Write-Error "Workflow file not found: $WorkflowFile"
    exit 1
}

$EventFile = ".github/events/templates/$EventType.json"
if (-not (Test-Path $EventFile)) {
    Write-Error "Event file not found: $EventFile"
    Write-Host "Available event types: push, pull_request"
    exit 1
}

# Install act if needed
Install-Act

# Build the act command
$ActCmd = "act"

# Add workflow file
$ActCmd += " -W $WorkflowFile"

# Add job if specified
if ($JobName) {
    $ActCmd += " -j $JobName"
}

# Add event type
$ActCmd += " -e $EventFile"

# Add common options
$ActCmd += " --bind --rm"

# Add platform configuration
$ActCmd += " -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"
$ActCmd += " -P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04"
$ActCmd += " -P ubuntu-20.04=ghcr.io/catthehacker/ubuntu:act-20.04"

# Print and run the command
Write-Host "Running: $ActCmd"
Invoke-Expression $ActCmd

# Install dependencies if not already installed
if (-not (Get-Command act -ErrorAction SilentlyContinue)) {
    Write-Host "Installing act..."
    winget install nektos.act
}

# Install Python dependencies
Write-Host "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install uv==$env:UV_VERSION
uv pip install -e ".[docs]" --system

# Run act with the specified parameters
Write-Host "Running act with parameters: $args"
act @args
