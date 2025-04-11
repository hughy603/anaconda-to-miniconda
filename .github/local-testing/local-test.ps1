# PowerShell script for testing GitHub Actions workflows locally
param(
    [Parameter(Mandatory=$true)][string]$WorkflowFile,
    [string]$EventType = "push",
    [string]$JobFilter = "",
    [string]$MatrixOverride = "",
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$AdditionalArgs
)

# Validate inputs
if (-not $WorkflowFile) {
    Write-Host "Usage: $PSCommandPath <workflow-file> [event-type] [job-filter] [matrix-override] [additional-args]"
    Write-Host "Examples:"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml pull_request"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml test"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml '' python-version=3.11"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml push '' '' --verbose"
    exit 1
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

# Build the command
$cmd = "act"

# Add workflow file
$cmd += " -W `"$WorkflowFile`""

# Add event file
$cmd += " -e `"$eventFile`""

# Add job filter if provided
if ($JobFilter) {
    $cmd += " --job `"$JobFilter`""
}

# Add matrix override if provided
if ($MatrixOverride) {
    # Create a temporary JSON file for matrix inputs
    Write-Host "Using matrix override: $MatrixOverride"

    # Parse matrix arguments
    $matrixParts = $MatrixOverride -split "="
    if ($matrixParts.Length -eq 2) {
        $key = $matrixParts[0]
        $value = $matrixParts[1]

        $matrixFile = ".github/local-testing/matrix-input.json"
        @{
            $key = $value
        } | ConvertTo-Json | Set-Content -Path $matrixFile

        $cmd += " --input-file `"$matrixFile`""
    }
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

# Add any additional arguments
if ($AdditionalArgs) {
    $cmd += " $($AdditionalArgs -join ' ')"
}

# Run the command
Write-Host "Running: $cmd"
Invoke-Expression $cmd
