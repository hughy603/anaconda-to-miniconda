# PowerShell script to set up GitHub Actions workflows for a project
# This script helps configure and customize workflows based on project type

param(
    [string]$ProjectType = "python",
    [string]$PythonVersion = "3.11",
    [switch]$UseUV = $true,
    [switch]$UseHatch = $true,
    [switch]$EnableCoverage = $true,
    [switch]$EnableSecurity = $true,
    [switch]$EnableDocs = $false,
    [switch]$Force = $false,
    [switch]$Help = $false
)

# Display help if requested
if ($Help) {
    Write-Host "Usage: .github/setup-workflows.ps1 [options]"
    Write-Host "Options:"
    Write-Host "  -ProjectType <type>    Project type (python, node, etc.) (default: python)"
    Write-Host "  -PythonVersion <ver>   Python version (default: 3.11)"
    Write-Host "  -UseUV                 Use UV for dependency management (default: true)"
    Write-Host "  -UseHatch              Use Hatch for project management (default: true)"
    Write-Host "  -EnableCoverage        Enable code coverage (default: true)"
    Write-Host "  -EnableSecurity        Enable security checks (default: true)"
    Write-Host "  -EnableDocs            Enable documentation workflow (default: false)"
    Write-Host "  -Force                 Overwrite existing files (default: false)"
    Write-Host "  -Help                  Display this help message"
    exit 0
}

# Ensure we're in the project root directory
$ProjectRoot = (Get-Location).Path

# Check if .github directory exists
if (-not (Test-Path "$ProjectRoot/.github")) {
    Write-Host "Creating .github directory..." -ForegroundColor Green
    New-Item -Path "$ProjectRoot/.github" -ItemType Directory -Force | Out-Null
}

# Check if .github/workflows directory exists
if (-not (Test-Path "$ProjectRoot/.github/workflows")) {
    Write-Host "Creating .github/workflows directory..." -ForegroundColor Green
    New-Item -Path "$ProjectRoot/.github/workflows" -ItemType Directory -Force | Out-Null
}

# Check if .github/actions directory exists
if (-not (Test-Path "$ProjectRoot/.github/actions")) {
    Write-Host "Creating .github/actions directory..." -ForegroundColor Green
    New-Item -Path "$ProjectRoot/.github/actions" -ItemType Directory -Force | Out-Null
}

# Function to copy and customize a file
function Copy-AndCustomize {
    param(
        [string]$SourcePath,
        [string]$DestPath,
        [hashtable]$Replacements
    )

    if ((Test-Path $DestPath) -and -not $Force) {
        Write-Host "File already exists: $DestPath" -ForegroundColor Yellow
        Write-Host "Use -Force to overwrite" -ForegroundColor Yellow
        return $false
    }

    if (-not (Test-Path $SourcePath)) {
        Write-Host "Source file not found: $SourcePath" -ForegroundColor Red
        return $false
    }

    # Create the destination directory if it doesn't exist
    $DestDir = Split-Path -Parent $DestPath
    if (-not (Test-Path $DestDir)) {
        New-Item -Path $DestDir -ItemType Directory -Force | Out-Null
    }

    # Copy the file
    Copy-Item -Path $SourcePath -Destination $DestPath -Force

    # Apply replacements
    $content = Get-Content -Path $DestPath -Raw
    foreach ($key in $Replacements.Keys) {
        $content = $content -replace $key, $Replacements[$key]
    }
    Set-Content -Path $DestPath -Value $content

    Write-Host "Created: $DestPath" -ForegroundColor Green
    return $true
}

# Function to copy a directory recursively
function Copy-DirectoryRecursive {
    param(
        [string]$SourceDir,
        [string]$DestDir,
        [hashtable]$Replacements
    )

    if (-not (Test-Path $SourceDir)) {
        Write-Host "Source directory not found: $SourceDir" -ForegroundColor Red
        return $false
    }

    # Create the destination directory if it doesn't exist
    if (-not (Test-Path $DestDir)) {
        New-Item -Path $DestDir -ItemType Directory -Force | Out-Null
    }

    # Copy all files in the source directory
    $files = Get-ChildItem -Path $SourceDir -File
    foreach ($file in $files) {
        $destPath = Join-Path -Path $DestDir -ChildPath $file.Name
        Copy-AndCustomize -SourcePath $file.FullName -DestPath $destPath -Replacements $Replacements
    }

    # Recursively copy subdirectories
    $dirs = Get-ChildItem -Path $SourceDir -Directory
    foreach ($dir in $dirs) {
        $destSubDir = Join-Path -Path $DestDir -ChildPath $dir.Name
        Copy-DirectoryRecursive -SourceDir $dir.FullName -DestDir $destSubDir -Replacements $Replacements
    }

    return $true
}

# Get project name from directory
$ProjectName = (Get-Item $ProjectRoot).Name

# Create replacements hashtable
$Replacements = @{
    "PYTHON_VERSION: `"3.11`"" = "PYTHON_VERSION: `"$PythonVersion`""
    "PROJECT_NAME" = $ProjectName
}

# Copy workflow configuration
Write-Host "Setting up workflow configuration..." -ForegroundColor Cyan
Copy-AndCustomize -SourcePath "$ProjectRoot/.github/workflow-config.yml" -DestPath "$ProjectRoot/.github/workflow-config.yml" -Replacements $Replacements

# Copy workflow templates based on project type
Write-Host "Setting up workflow templates for $ProjectType..." -ForegroundColor Cyan
$TemplateDir = "$ProjectRoot/.github/templates/$ProjectType"
if (Test-Path $TemplateDir) {
    # Copy CI workflow
    Copy-AndCustomize -SourcePath "$TemplateDir/ci.yml" -DestPath "$ProjectRoot/.github/workflows/ci.yml" -Replacements $Replacements

    # Copy other workflows if needed
    if ($EnableDocs) {
        if (Test-Path "$TemplateDir/docs.yml") {
            Copy-AndCustomize -SourcePath "$TemplateDir/docs.yml" -DestPath "$ProjectRoot/.github/workflows/docs.yml" -Replacements $Replacements
        }
    }
} else {
    Write-Host "Template directory not found: $TemplateDir" -ForegroundColor Red
    Write-Host "Please ensure the template directory exists for the specified project type" -ForegroundColor Red
    exit 1
}

# Copy composite actions
Write-Host "Setting up composite actions..." -ForegroundColor Cyan
Copy-DirectoryRecursive -SourceDir "$ProjectRoot/.github/actions" -DestDir "$ProjectRoot/.github/actions" -Replacements $Replacements

# Create local testing directory if it doesn't exist
if (-not (Test-Path "$ProjectRoot/.github/local-testing")) {
    Write-Host "Creating local testing directory..." -ForegroundColor Green
    New-Item -Path "$ProjectRoot/.github/local-testing" -ItemType Directory -Force | Out-Null
    New-Item -Path "$ProjectRoot/.github/local-testing/events" -ItemType Directory -Force | Out-Null
}

# Create sample event files for local testing
$PushEvent = @"
{
  "ref": "refs/heads/main",
  "before": "0000000000000000000000000000000000000000",
  "after": "1111111111111111111111111111111111111111",
  "repository": {
    "name": "$ProjectName",
    "full_name": "username/$ProjectName",
    "private": false
  },
  "pusher": {
    "name": "username",
    "email": "username@example.com"
  },
  "sender": {
    "login": "username"
  }
}
"@
Set-Content -Path "$ProjectRoot/.github/local-testing/events/push.json" -Value $PushEvent

$PullRequestEvent = @"
{
  "action": "opened",
  "number": 1,
  "pull_request": {
    "number": 1,
    "state": "open",
    "title": "Test PR",
    "body": "This is a test PR",
    "head": {
      "ref": "feature-branch",
      "sha": "2222222222222222222222222222222222222222"
    },
    "base": {
      "ref": "main",
      "sha": "1111111111111111111111111111111111111111"
    }
  },
  "repository": {
    "name": "$ProjectName",
    "full_name": "username/$ProjectName",
    "private": false
  },
  "sender": {
    "login": "username"
  }
}
"@
Set-Content -Path "$ProjectRoot/.github/local-testing/events/pull_request.json" -Value $PullRequestEvent

# Create .actrc file if it doesn't exist
if (-not (Test-Path "$ProjectRoot/.actrc")) {
    $ActrcContent = @"
-P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
-P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04
-P ubuntu-20.04=ghcr.io/catthehacker/ubuntu:act-20.04
-P windows-latest=ghcr.io/catthehacker/ubuntu:act-latest
-P macos-latest=ghcr.io/catthehacker/ubuntu:act-latest
"@
    Set-Content -Path "$ProjectRoot/.actrc" -Value $ActrcContent
    Write-Host "Created .actrc file for local testing" -ForegroundColor Green
}

Write-Host "Workflow setup completed successfully!" -ForegroundColor Green
Write-Host "You can now run your workflows locally with:" -ForegroundColor Cyan
Write-Host "  act -W .github/workflows/ci.yml" -ForegroundColor Cyan
Write-Host "Or on GitHub by pushing to your repository" -ForegroundColor Cyan
