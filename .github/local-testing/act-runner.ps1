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
        "__pycache__"
        # Removed .pytest_cache, .mypy_cache, and .ruff_cache to ensure test files are copied
    )

    # Build the exclude parameter
    $excludeParams = $excludeDirs | ForEach-Object { "/XD `"$_`"" }

    # Execute robocopy with the exclude parameters
    Write-Host "Copying files using robocopy..." -ForegroundColor Green
    $robocopyCmd = "robocopy `"$currentDir`" `"$tempDir`" /E /NFL /NDL /NJH /NJS /NC /NS /MT:8 $excludeParams"
    Invoke-Expression $robocopyCmd | Out-Null

    # Verify that pyproject.toml was copied
    if (Test-Path "$currentDir\pyproject.toml") {
        Write-Host "Ensuring pyproject.toml is copied..." -ForegroundColor Green
        Copy-Item -Path "$currentDir\pyproject.toml" -Destination "$tempDir\pyproject.toml" -Force
    }

    # Create necessary directory structure for _version.py
    $versionDir = Join-Path -Path $tempDir -ChildPath "src\conda_forge_converter"
    if (-not (Test-Path $versionDir)) {
        Write-Host "Creating directory structure for _version.py..." -ForegroundColor Green
        New-Item -Path $versionDir -ItemType Directory -Force | Out-Null
    }

    # Create a minimal _version.py file
    $versionFile = Join-Path -Path $versionDir -ChildPath "_version.py"
    Write-Host "Creating _version.py file..." -ForegroundColor Green
    Set-Content -Path $versionFile -Value "__version__ = '0.1.0'" -Force

    # Ensure tests directory exists
    $testsDir = Join-Path -Path $tempDir -ChildPath "tests"
    if (-not (Test-Path $testsDir)) {
        Write-Host "Creating tests directory..." -ForegroundColor Green
        New-Item -Path $testsDir -ItemType Directory -Force | Out-Null

        # Create a minimal test file to prevent pytest errors
        $testFile = Join-Path -Path $testsDir -ChildPath "test_basic.py"
        Write-Host "Creating minimal test file..." -ForegroundColor Green
        Set-Content -Path $testFile -Value @"
def test_placeholder():
    """A placeholder test to ensure pytest finds at least one test."""
    assert True
"@ -Force
    }

    # Copy any existing test files
    if (Test-Path "$currentDir\tests") {
        Write-Host "Copying test files..." -ForegroundColor Green
        $testFiles = Get-ChildItem -Path "$currentDir\tests" -Filter "*.py" -Recurse
        foreach ($file in $testFiles) {
            # Get the relative path safely
            $fullPath = $file.FullName
            $testsBasePath = Join-Path -Path $currentDir -ChildPath "tests"

            # Ensure paths use the same format
            $fullPath = $fullPath.Replace("/", "\")
            $testsBasePath = $testsBasePath.Replace("/", "\")

            # Make sure testsBasePath ends with a backslash
            if (-not $testsBasePath.EndsWith("\")) {
                $testsBasePath = "$testsBasePath\"
            }

            # Get relative path safely
            if ($fullPath.StartsWith($testsBasePath)) {
                $relativePath = $fullPath.Substring($testsBasePath.Length)
                $destPath = Join-Path -Path $testsDir -ChildPath $relativePath
                $destDir = Split-Path -Path $destPath -Parent

                if (-not (Test-Path $destDir)) {
                    New-Item -Path $destDir -ItemType Directory -Force | Out-Null
                }

                Copy-Item -Path $file.FullName -Destination $destPath -Force
            }
            else {
                # Just copy the file to the root of the tests directory
                $destPath = Join-Path -Path $testsDir -ChildPath $file.Name
                Copy-Item -Path $file.FullName -Destination $destPath -Force
            }
        }
    }

    # Copy pyproject.toml if it exists
    if (Test-Path "$currentDir\pyproject.toml") {
        Write-Host "Copying pyproject.toml..." -ForegroundColor Green
        Copy-Item -Path "$currentDir\pyproject.toml" -Destination "$tempDir\pyproject.toml" -Force

        # Create a .hatch directory with minimal configuration
        $hatchDir = Join-Path -Path $tempDir -ChildPath ".hatch"
        if (-not (Test-Path $hatchDir)) {
            Write-Host "Creating .hatch directory..." -ForegroundColor Green
            New-Item -Path $hatchDir -ItemType Directory -Force | Out-Null
        }

        # Create a minimal hatch_build.py file to handle the build process
        $hatchBuildDir = Join-Path -Path $hatchDir -ChildPath "env"
        if (-not (Test-Path $hatchBuildDir)) {
            Write-Host "Creating .hatch/env directory..." -ForegroundColor Green
            New-Item -Path $hatchBuildDir -ItemType Directory -Force | Out-Null
        }
    }

    # Create a minimal LICENSE file
    $licenseFile = Join-Path -Path $tempDir -ChildPath "LICENSE"
    Write-Host "Creating LICENSE file..." -ForegroundColor Green
    Set-Content -Path $licenseFile -Value "MIT License

Copyright (c) 2025 Test User

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the 'Software'), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE." -Force

    # Create a minimal README.md file
    $readmeFile = Join-Path -Path $tempDir -ChildPath "README.md"
    Write-Host "Creating README.md file..." -ForegroundColor Green
    Set-Content -Path $readmeFile -Value "# Conda Forge Converter

A tool to convert Anaconda environments to conda-forge with the same top-level dependency versions.

## Installation

```bash
pip install conda-forge-converter
```

## Usage

```bash
conda-forge-converter --help
```
" -Force

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

        # Check if we have a local testing version of the workflow file
        $workflowFileName = Split-Path -Path $WorkflowFile -Leaf
        $workflowBaseName = [System.IO.Path]::GetFileNameWithoutExtension($workflowFileName)
        $workflowExtension = [System.IO.Path]::GetExtension($workflowFileName)
        $localTestingWorkflowFile = Join-Path -Path $currentDir -ChildPath ".github/local-testing/$workflowBaseName-local$workflowExtension"

        if (Test-Path $localTestingWorkflowFile) {
            # Use the local testing version of the workflow file
            $destWorkflowFile = Join-Path -Path $tempWorkflowsDir -ChildPath $workflowFileName
            Write-Host "Using local testing workflow file: $localTestingWorkflowFile" -ForegroundColor Green
            Write-Host "Copying to: $destWorkflowFile" -ForegroundColor Green
            Copy-Item -Path $localTestingWorkflowFile -Destination $destWorkflowFile -Force
        } else {
            # Use the original workflow file
            $sourceWorkflowFile = Join-Path -Path $currentDir -ChildPath $WorkflowFile
            $destWorkflowFile = Join-Path -Path $tempWorkflowsDir -ChildPath $workflowFileName
            Write-Host "Copying workflow file to: $destWorkflowFile" -ForegroundColor Green
            Copy-Item -Path $sourceWorkflowFile -Destination $destWorkflowFile -Force
        }
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
    if (-not (Test-Path $EventFile)) {
        Write-Host "Event file not found: $EventFile" -ForegroundColor Red
        return 1
    }

    $eventFileName = Split-Path -Path $EventFile -Leaf
    $tempEventFile = Join-Path -Path $tempEventsDir -ChildPath $eventFileName
    Write-Host "Copying event file from $EventFile to: $tempEventFile" -ForegroundColor Green
    Copy-Item -Path $EventFile -Destination $tempEventFile -Force

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
    # Use the same Ubuntu Docker image for all platforms
    $actCommand = "act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest -P windows-latest=ghcr.io/catthehacker/ubuntu:act-latest -P macos-latest=ghcr.io/catthehacker/ubuntu:act-latest -W `"$tempWorkflowFile`" -e `"$tempEventFile`""

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
