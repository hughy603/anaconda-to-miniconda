# PowerShell script to run GitHub Actions locally using act
# This script consolidates the functionality of multiple previous scripts
param(
    [Parameter(Mandatory=$true)][string]$WorkflowFile,
    [string]$EventFile,
    [string]$MatrixFile = "",
    [string]$Platform = "ubuntu-latest",
    [string]$DockerImage = "ghcr.io/catthehacker/ubuntu:act-latest",
    [switch]$KeepTemp = $false,
    [string]$JobFilter = "",
    [switch]$DryRun = $false
)

# Display script information
Write-Host "GitHub Actions Local Runner" -ForegroundColor Cyan
Write-Host "------------------------" -ForegroundColor Cyan

# Get the current directory and user's home directory
$currentDir = Get-Location
$homeDir = $env:USERPROFILE
Write-Host "Current directory: $currentDir"
Write-Host "Home directory: $homeDir"

# Create a temporary directory in the user's home directory
$tempDir = Join-Path -Path $homeDir -ChildPath "act-temp"
if (Test-Path $tempDir) {
    Write-Host "Removing existing temporary directory: $tempDir" -ForegroundColor Yellow
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "Creating temporary directory: $tempDir" -ForegroundColor Green
New-Item -Path $tempDir -ItemType Directory -Force | Out-Null

try {
    # Copy the repository files to the temporary directory
    Write-Host "Copying repository files to temporary directory..." -ForegroundColor Green

    # Check if Docker is running (skip if DryRun is specified)
    if (-not $DryRun) {
        try {
            $dockerStatus = docker info 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
                Write-Host "If you want to test the script without Docker, use the -DryRun switch." -ForegroundColor Yellow
                return 1
            }
        }
        catch {
            Write-Host "Docker is not installed or not in PATH. Please install Docker Desktop and try again." -ForegroundColor Red
            Write-Host "If you want to test the script without Docker, use the -DryRun switch." -ForegroundColor Yellow
            return 1
        }
    }
    else {
        Write-Host "Running in dry-run mode. Docker will not be used." -ForegroundColor Yellow
    }

    # Use robocopy for more reliable copying on Windows
    # /E = Copy subdirectories, including empty ones
    # /NFL = No file list - don't log file names
    # /NDL = No directory list - don't log directory names
    # /NJH = No job header
    # /NJS = No job summary
    # /NC = No class - don't log file classes
    # /NS = No size - don't log file sizes
    # /MT = Multi-threaded copying

    # Create a list of directories to exclude
    $excludeDirs = @(
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache"
    )

    # Build the exclude parameter
    $excludeParams = $excludeDirs | ForEach-Object { "/XD `"$_`"" }

    # Execute robocopy with the exclude parameters
    Write-Host "Copying files using robocopy..." -ForegroundColor Green
    $robocopyCmd = "robocopy `"$currentDir`" `"$tempDir`" /E /NFL /NDL /NJH /NJS /NC /NS /MT:8 $excludeParams"
    Invoke-Expression $robocopyCmd | Out-Null

    # Make sure the .github directory exists
    $tempGithubDir = Join-Path -Path $tempDir -ChildPath ".github"
    if (-not (Test-Path $tempGithubDir)) {
        Write-Host "Creating .github directory" -ForegroundColor Yellow
        New-Item -Path $tempGithubDir -ItemType Directory -Force | Out-Null
    }

    # Make sure the .github/workflows directory exists
    $tempWorkflowsDir = Join-Path -Path $tempGithubDir -ChildPath "workflows"
    if (-not (Test-Path $tempWorkflowsDir)) {
        Write-Host "Creating .github/workflows directory" -ForegroundColor Yellow
        New-Item -Path $tempWorkflowsDir -ItemType Directory -Force | Out-Null

        # Copy the workflow file directly
        $workflowFileName = Split-Path -Path $WorkflowFile -Leaf
        $sourceWorkflowFile = Join-Path -Path $currentDir -ChildPath $WorkflowFile
        $destWorkflowFile = Join-Path -Path $tempWorkflowsDir -ChildPath $workflowFileName
        Write-Host "Copying workflow file to: $destWorkflowFile" -ForegroundColor Green
        Copy-Item -Path $sourceWorkflowFile -Destination $destWorkflowFile -Force
    }

    # Make sure the .github/local-testing directory exists
    $tempLocalTestingDir = Join-Path -Path $tempGithubDir -ChildPath "local-testing"
    if (-not (Test-Path $tempLocalTestingDir)) {
        Write-Host "Creating .github/local-testing directory" -ForegroundColor Yellow
        New-Item -Path $tempLocalTestingDir -ItemType Directory -Force | Out-Null
    }

    # Make sure the .github/local-testing/events directory exists
    $tempEventsDir = Join-Path -Path $tempDir -ChildPath ".github/local-testing/events"
    if (-not (Test-Path $tempEventsDir)) {
        New-Item -Path $tempEventsDir -ItemType Directory -Force | Out-Null
    }

    # Verify the workflow file exists
    $workflowFileName = Split-Path -Path $WorkflowFile -Leaf
    $tempWorkflowFilePath = Join-Path -Path $tempWorkflowsDir -ChildPath $workflowFileName
    if (-not (Test-Path $tempWorkflowFilePath)) {
        Write-Host "Workflow file not found: $tempWorkflowFilePath" -ForegroundColor Red
        Write-Host "Copying workflow file directly..." -ForegroundColor Yellow
        $sourceWorkflowFile = Join-Path -Path $currentDir -ChildPath $WorkflowFile
        Copy-Item -Path $sourceWorkflowFile -Destination $tempWorkflowFilePath -Force
    }

    # Make sure the event file exists in the temporary directory
    $eventFileName = Split-Path -Path $EventFile -Leaf
    $tempEventFile = Join-Path -Path $tempEventsDir -ChildPath $eventFileName
    if (-not (Test-Path $tempEventFile)) {
        Write-Host "Copying event file to: $tempEventFile" -ForegroundColor Green
        Copy-Item -Path $EventFile -Destination $tempEventFile -Force
    }

    # Copy the matrix file if provided
    if ($MatrixFile -ne "") {
        $matrixFileName = Split-Path -Path $MatrixFile -Leaf
        $tempMatrixFile = Join-Path -Path $tempDir -ChildPath ".github/local-testing/$matrixFileName"
        if (-not (Test-Path $tempMatrixFile)) {
            Write-Host "Copying matrix file to: $tempMatrixFile" -ForegroundColor Green
            Copy-Item -Path $MatrixFile -Destination $tempMatrixFile -Force
        }
    }

    # Change to the temporary directory
    Set-Location $tempDir
    Write-Host "Changed to temporary directory: $(Get-Location)" -ForegroundColor Green

    # Initialize a git repository
    Write-Host "Initializing git repository..." -ForegroundColor Green
    git init -q
    git add .
    git config --global user.email "act@example.com" 2>$null
    git config --global user.name "Act Runner" 2>$null
    git commit -q -m "Initial commit for act"

    # Convert paths to use forward slashes for act
    $tempWorkflowFile = ".github/workflows/$workflowFileName"
    $tempEventFile = ".github/local-testing/events/$eventFileName"
    $tempMatrixFile = if ($MatrixFile -ne "") { ".github/local-testing/$matrixFileName" } else { "" }

    # Build the command with platform mapping
    $actCommand = "act -P $Platform=$DockerImage -W `"$tempWorkflowFile`" -e `"$tempEventFile`""

    # Add job filter if provided
    if ($JobFilter -ne "") {
        $actCommand += " --job $JobFilter"
    }

    # Add matrix file if provided
    if ($tempMatrixFile -ne "") {
        $actCommand += " --input-file `"$tempMatrixFile`""
    }

    # Execute act (skip if DryRun is specified)
    Write-Host "Running: $actCommand" -ForegroundColor Green
    Write-Host "------------------------" -ForegroundColor Cyan

    if (-not $DryRun) {
        Invoke-Expression $actCommand
    }
    else {
        Write-Host "Dry run mode: Command would be executed here" -ForegroundColor Yellow
        Write-Host "To run with Docker, remove the -DryRun switch" -ForegroundColor Yellow
    }
    $exitCode = $LASTEXITCODE
    Write-Host "------------------------" -ForegroundColor Cyan

    # Return the exit code
    if ($exitCode -eq 0) {
        Write-Host "Act completed successfully" -ForegroundColor Green
    } else {
        Write-Host "Act failed with exit code $exitCode" -ForegroundColor Red
    }

    return $exitCode
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    return 1
}
finally {
    # Return to original directory
    Set-Location $currentDir

    # Clean up temporary directory unless KeepTemp is specified
    if (-not $KeepTemp) {
        Write-Host "Cleaning up temporary directory" -ForegroundColor Yellow
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "Keeping temporary directory: $tempDir" -ForegroundColor Yellow
    }
}
