# PowerShell script for running GitHub Actions workflows locally using act
# This follows industry standard practices for local GitHub Actions testing

# Parse command line arguments
param(
    [Parameter(Mandatory = $false)][string]$WorkflowFile,
    [string]$EventType = "push",
    [string]$JobFilter = "",
    [string]$Platform = "ubuntu-latest",
    [switch]$Bind = $false,
    [switch]$VerboseOutput = $false,
    [switch]$Help = $false
)

# Display help information
function Show-Help {
    Write-Host "GitHub Actions Local Testing" -ForegroundColor Cyan
    Write-Host "Usage: $PSCommandPath [options]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -WorkflowFile FILE     Workflow file to run (required)"
    Write-Host "  -EventType TYPE        Event type to trigger (default: push)"
    Write-Host "  -JobFilter JOB         Run specific job"
    Write-Host "  -Platform PLATFORM     Platform to run on (default: ubuntu-latest)"
    Write-Host "  -Bind                  Bind working directory to act container"
    Write-Host "  -VerboseOutput         Enable verbose output"
    Write-Host "  -Help                  Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  $PSCommandPath -WorkflowFile .github/workflows/ci.yml"
    Write-Host "  $PSCommandPath -WorkflowFile .github/workflows/ci.yml -EventType pull_request"
    Write-Host "  $PSCommandPath -WorkflowFile .github/workflows/ci.yml -JobFilter build"
    Write-Host ""
    Write-Host "Note: This script assumes act is installed and Docker is running."
}
# Show help if requested
if ($Help -or (-not $WorkflowFile)) {
    Show-Help
    exit
}

# Check if act is installed
$actInstalled = $null
try {
    $actInstalled = Get-Command act -ErrorAction SilentlyContinue
}
catch {
    $actInstalled = $null
}

if (-not $actInstalled) {
    Write-Host "Error: act is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "https://github.com/nektos/act#installation" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    $dockerRunning = $false
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
    }

    if (-not $dockerRunning) {
        Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "Error: Docker is not installed or not in PATH. Please install Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Create events directory if it doesn't exist
$eventsDir = ".github/events"
if (-not (Test-Path $eventsDir)) {
    New-Item -Path $eventsDir -ItemType Directory -Force | Out-Null
}

# Create event file if it doesn't exist
$eventFile = "$eventsDir/$EventType.json"
if (-not (Test-Path $eventFile)) {
    $templateFile = ".github/events/templates/$EventType.json"

    # Check if we have a template for this event type
    if (Test-Path $templateFile) {
        Write-Host "Creating $EventType event from template..." -ForegroundColor Green
        Copy-Item -Path $templateFile -Destination $eventFile
    }
    else {
        Write-Host "Creating basic $EventType event..." -ForegroundColor Green
        @{
            "event_type" = $EventType
        } | ConvertTo-Json | Set-Content -Path $eventFile

        # If this is a pull_request event, warn about using the template
        if ($EventType -eq "pull_request") {
            Write-Host "Warning: Pull request events require detailed context." -ForegroundColor Yellow
            Write-Host "Consider using the provided template by running:" -ForegroundColor Yellow
            Write-Host "Copy-Item -Path .github/events/templates/pull_request.json -Destination .github/events/pull_request.json" -ForegroundColor Yellow
        }
    }
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

# Add platform mappings
$cmd += " -P $Platform=ghcr.io/catthehacker/ubuntu:act-latest"

# Add bind option if specified
if ($Bind) {
    $cmd += " --bind"
}

# Add verbose option if specified
if ($VerboseOutput) {
    $cmd += " --verbose"
}

# Set environment variables for local testing
$cmd += " --env ACT=true"
$cmd += " --env ACT_LOCAL_TESTING=true"
$cmd += " --env GITHUB_TOKEN=local-testing-token"
$cmd += " -s GITHUB_TOKEN=local-testing-token"

# Display the command
Write-Host "Running: $cmd" -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Cyan

# Run the command safely without Invoke-Expression
$cmdArgs = $cmd -replace '^act\s+', ''  # Remove 'act' from the beginning
& act $cmdArgs.Split(' ')

# Display completion message
Write-Host "-----------------------------------" -ForegroundColor Cyan
Write-Host "Local testing completed!" -ForegroundColor Green
