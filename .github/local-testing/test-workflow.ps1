# PowerShell script to test GitHub Actions workflows
#
# This script allows you to test GitHub Actions workflows locally using act.
# It handles creating event files, matrix overrides, and running the workflow.
#
# Examples:
#   - Test the CI workflow:
#     .\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml
#
#   - Test with a specific event type:
#     .\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -EventType pull_request
#
#   - Test with a matrix override:
#     .\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -MatrixOverride "python-version=3.11"
#
#   - Test a specific job:
#     .\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -JobFilter "test"
#
#   - Dry run (don't actually run Docker):
#     .\test-workflow.ps1 -WorkflowFile .github/workflows/ci.yml -DryRun
#
param(
    [Parameter(Mandatory=$true)][string]$WorkflowFile,
    [string]$EventType = "push",
    [string]$MatrixOverride = "",
    [string]$Platform = "ubuntu-latest",
    [string]$DockerImage = "ghcr.io/catthehacker/ubuntu:act-latest",
    [string]$JobFilter = "",
    [switch]$DryRun = $false
)

# Create events directory if it doesn't exist
$eventsDir = ".github/local-testing/events"
if (-not (Test-Path $eventsDir)) {
    New-Item -Path $eventsDir -ItemType Directory -Force | Out-Null
}

# Create a simple event file if it doesn't exist
$eventFile = "$eventsDir/$EventType.json"
if (-not (Test-Path $eventFile)) {
    Write-Host "Creating sample $EventType event..." -ForegroundColor Yellow
    @{
        "event_type" = $EventType
    } | ConvertTo-Json | Set-Content -Path $eventFile
}

# Handle matrix override
if ($MatrixOverride -ne "") {
    Write-Host "Using matrix override: $MatrixOverride" -ForegroundColor Cyan

    # Parse matrix arguments
    $matrixParts = $MatrixOverride -split "="
    if ($matrixParts.Length -eq 2) {
        $key = $matrixParts[0]
        $value = $matrixParts[1]

        # Create a temporary JSON file for matrix inputs
        $matrixJson = @{
            $key = $value
        } | ConvertTo-Json

        $matrixFile = ".github/local-testing/matrix-input.json"
        Set-Content -Path $matrixFile -Value $matrixJson

        # Run act with matrix override
        Write-Host "Testing workflow: $WorkflowFile with event: $EventType and matrix: $MatrixOverride" -ForegroundColor Green
        & "$PSScriptRoot\act-runner.ps1" -WorkflowFile $WorkflowFile -EventFile $eventFile -MatrixFile $matrixFile -Platform $Platform -DockerImage $DockerImage -JobFilter $JobFilter -DryRun:$DryRun
    }
    else {
        Write-Host "Invalid matrix override format. Expected key=value." -ForegroundColor Red
        exit 1
    }
}
else {
    # Run without matrix override
    Write-Host "Testing workflow: $WorkflowFile with event: $EventType" -ForegroundColor Green

    # Ensure the event file exists and is accessible
    if (-not (Test-Path $eventFile)) {
        Write-Error "Event file not found: $eventFile"
        exit 1
    }

    & "$PSScriptRoot\act-runner.ps1" -WorkflowFile $WorkflowFile -EventFile $eventFile -Platform $Platform -DockerImage $DockerImage -JobFilter $JobFilter -DryRun:$DryRun
}
