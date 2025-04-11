# PowerShell script for testing GitHub Actions workflows locally
param(
    [string]$WorkflowFile = ".github/workflows/ci.yml",
    [string]$EventType = "push",
    [string]$JobFilter = "",
    [string]$PythonVersion = "",
    [switch]$SkipDocker = $false,
    [switch]$Help = $false
)

# Display help if requested
if ($Help) {
    Write-Host "Usage: $PSCommandPath [options]"
    Write-Host "Options:"
    Write-Host "  -WorkflowFile FILE    Workflow file to test (default: .github/workflows/ci.yml)"
    Write-Host "  -EventType TYPE       Event type (default: push)"
    Write-Host "  -JobFilter NAME       Job to run (default: all jobs)"
    Write-Host "  -PythonVersion VER    Python version to test (default: use matrix)"
    Write-Host "  -SkipDocker           Skip Docker and run tests directly with local Python"
    exit 0
}

# Create event file if it doesn't exist
$eventsDir = ".github/local-testing/events"
if (-not (Test-Path $eventsDir)) {
    New-Item -Path $eventsDir -ItemType Directory -Force | Out-Null
}

$eventFile = "$eventsDir/$EventType.json"
if (-not (Test-Path $eventFile)) {
    Write-Host "Creating sample $EventType event..."
    @{
        "event_type" = $EventType
    } | ConvertTo-Json | Set-Content -Path $eventFile
}

if ($SkipDocker) {
    Write-Host "Running tests directly with local Python..."

    # Extract test commands from workflow
    $workflowContent = Get-Content -Path $WorkflowFile -Raw
    if ($workflowContent -match "Run tests[\s\S]*?run:([\s\S]*?)(?:\n\s*-|\n\s*$)") {
        $testCommand = $matches[1].Trim()

        if ($PythonVersion) {
            Write-Host "Testing with Python $PythonVersion..."
            # Use poetry to run tests with specific Python version
            poetry env use $PythonVersion
            poetry install

            # Extract the actual command from the multiline string
            $testCommand = $testCommand -replace '^\s*\|\s*', '' -replace '\n\s*\|\s*', ' '
            Invoke-Expression "poetry run $testCommand"
        }
        else {
            Write-Host "Testing with default Python version..."
            poetry install

            # Extract the actual command from the multiline string
            $testCommand = $testCommand -replace '^\s*\|\s*', '' -replace '\n\s*\|\s*', ' '
            Invoke-Expression "poetry run $testCommand"
        }
    }
    else {
        Write-Host "Could not find test command in workflow file. Running default test command..."
        poetry install
        poetry run pytest
    }
}
else {
    # Build the act command
    $cmd = "act"

    # Add workflow file
    $cmd += " -W `"$WorkflowFile`""

    # Add event file
    $cmd += " -e `"$eventFile`""

    # Add job filter if provided
    if ($JobFilter) {
        $cmd += " --job `"$JobFilter`""
    }

    # Add matrix override if Python version is provided
    if ($PythonVersion) {
        Write-Host "Using Python version: $PythonVersion"
        $matrixFile = ".github/local-testing/matrix-input.json"
        @{
            "python-version" = $PythonVersion
        } | ConvertTo-Json | Set-Content -Path $matrixFile

        $cmd += " --input-file `"$matrixFile`""
    }

    # Add platform mappings
    $cmd += " -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"
    $cmd += " -P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04"
    $cmd += " -P ubuntu-20.04=ghcr.io/catthehacker/ubuntu:act-20.04"
    $cmd += " -P windows-latest=ghcr.io/catthehacker/ubuntu:act-latest"
    $cmd += " -P macos-latest=ghcr.io/catthehacker/ubuntu:act-latest"

    # Set environment variables for local testing
    $cmd += " --env ACT_LOCAL_TESTING=true"
    $cmd += " --env SKIP_DOCKER_BUILDS=true"
    $cmd += " --env SKIP_LONG_RUNNING_TESTS=true"

    # Run the command
    Write-Host "Running: $cmd"
    Invoke-Expression $cmd
}
