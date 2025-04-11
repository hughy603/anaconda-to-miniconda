# PowerShell script for testing GitHub Actions workflows with Python 3.11 and 3.12
# This script combines the functionality of multiple scripts into one

param(
    [string]$WorkflowFile = ".github/workflows/ci.yml",
    [string]$EventType = "push",
    [string]$JobFilter = "",
    [string]$PythonVersion = "",
    [switch]$BothVersions = $false,
    [switch]$SkipDocker = $false,
    [switch]$ValidateOnly = $false,
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
    Write-Host "  -BothVersions         Test with both Python 3.11 and 3.12"
    Write-Host "  -SkipDocker           Skip Docker and run tests directly with local Python"
    Write-Host "  -ValidateOnly         Validate workflow file only"
    exit 0
}

# Function to validate workflow file
function Validate-Workflow {
    param(
        [string]$WorkflowFile
    )

    Write-Host "Validating workflow: $WorkflowFile" -ForegroundColor Cyan

    # Check if actionlint is installed
    $actionlintInstalled = $null
    try {
        $actionlintInstalled = Get-Command actionlint -ErrorAction SilentlyContinue
    } catch {
        $actionlintInstalled = $null
    }

    if ($actionlintInstalled) {
        Write-Host "Running actionlint..." -ForegroundColor Green
        actionlint $WorkflowFile
        $actionlintExit = $LASTEXITCODE
        if ($actionlintExit -ne 0) {
            Write-Host "actionlint found issues in the workflow file." -ForegroundColor Yellow
            return $false
        }
    } else {
        Write-Host "Warning: actionlint not found. Install with: 'go install github.com/rhysd/actionlint/cmd/actionlint@latest'" -ForegroundColor Yellow
        Write-Host "Continuing with basic checks..." -ForegroundColor Yellow
    }

    Write-Host "Running custom checks..." -ForegroundColor Green

    # Read workflow content
    $workflowContent = Get-Content -Path $WorkflowFile -Raw

    # Check for Python version matrix
    if ($workflowContent -match "matrix:") {
        Write-Host "Matrix strategy found" -ForegroundColor Green

        if ($workflowContent -match "python-version:") {
            Write-Host "Python versions specified in matrix" -ForegroundColor Green

            # Check if Python 3.11 and 3.12 are included
            if ($workflowContent -notmatch "3\.11") {
                Write-Host "WARNING: Matrix should include Python 3.11" -ForegroundColor Yellow
            }

            if ($workflowContent -notmatch "3\.12") {
                Write-Host "WARNING: Matrix should include Python 3.12" -ForegroundColor Yellow
            }
        } else {
            Write-Host "WARNING: Matrix strategy found but no Python versions specified" -ForegroundColor Yellow
        }
    } else {
        Write-Host "WARNING: No matrix strategy found in workflow" -ForegroundColor Yellow
    }

    # Check for conditional execution for local testing
    # Skip this check for validate-workflows.yml since we've already added the condition
    if ($WorkflowFile -notmatch "validate-workflows\.yml" -and $workflowContent -notmatch "ACT_LOCAL_TESTING") {
        Write-Host "WARNING: Workflow does not have conditional execution for local testing" -ForegroundColor Yellow
        Write-Host "Consider adding: if: `${{ env.ACT_LOCAL_TESTING != 'true' }} for steps that shouldn't run locally" -ForegroundColor Yellow
    }

    # Check for deprecated actions
    # First, filter out lines that are part of validation checks (grep or if statements)
    $actionLines = $workflowContent -split "`n" | Where-Object {
        $_ -match "uses: actions/" -and
        $_ -notmatch "grep" -and
        $_ -notmatch "if.*uses: actions/"
    }
    
    $usesDeprecatedActions = $false
    foreach ($line in $actionLines) {
        if ($line -match "@master") {
            $usesDeprecatedActions = $true
            Write-Host "Found deprecated action: $line" -ForegroundColor Yellow
        }
    }
    
    if ($usesDeprecatedActions) {
        Write-Host "ERROR: Uses actions with @master tag instead of version tag" -ForegroundColor Red
        Write-Host "Replace @master with specific version tags like @v4" -ForegroundColor Yellow
        return $false
    }

    Write-Host "Validation complete" -ForegroundColor Green
    return $true
}

# Function to run tests with a specific Python version
function Run-TestsWithPython {
    param(
        [string]$PythonVersion
    )

    Write-Host "Testing with Python $PythonVersion..." -ForegroundColor Green
    Write-Host "----------------------------------------" -ForegroundColor Green

    if ($SkipDocker) {
        Write-Host "Running tests directly with Python $PythonVersion..." -ForegroundColor Green

        # Check if the Python version is available
        $pythonInstalled = $null
        try {
            $pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
        } catch {
            $pythonInstalled = $null
        }

        if (-not $pythonInstalled) {
            Write-Host "Python not found. Please install Python or use Docker." -ForegroundColor Red
            return $false
        }

        # Use hatch or poetry based on what's available
        $hatchInstalled = $null
        $poetryInstalled = $null

        try {
            $hatchInstalled = Get-Command hatch -ErrorAction SilentlyContinue
        } catch {
            $hatchInstalled = $null
        }

        try {
            $poetryInstalled = Get-Command poetry -ErrorAction SilentlyContinue
        } catch {
            $poetryInstalled = $null
        }

        if ($hatchInstalled) {
            Write-Host "Using hatch to run tests..." -ForegroundColor Green
            hatch env create python$PythonVersion
            hatch run test
        } elseif ($poetryInstalled) {
            Write-Host "Using poetry to run tests..." -ForegroundColor Green
            poetry env use $PythonVersion
            poetry install
            poetry run pytest
        } else {
            Write-Host "Neither hatch nor poetry found. Using system Python..." -ForegroundColor Yellow
            python -m pytest
        }

        $testExit = $LASTEXITCODE
        return ($testExit -eq 0)
    } else {
        # Create event file if it doesn't exist
        $eventsDir = ".github/local-testing/events"
        if (-not (Test-Path $eventsDir)) {
            New-Item -Path $eventsDir -ItemType Directory -Force | Out-Null
        }

        # For validate-workflows.yml, use workflow_dispatch event
        if ($WorkflowFile -match "validate-workflows\.yml" -and (Test-Path "$eventsDir/workflow_dispatch.json")) {
            $eventFile = "$eventsDir/workflow_dispatch.json"
            $EventType = "workflow_dispatch"
        } else {
            $eventFile = "$eventsDir/$EventType.json"
        }
        
        if (-not (Test-Path $eventFile)) {
            Write-Host "Creating sample $EventType event..." -ForegroundColor Green
            @{
                "event_type" = $EventType
            } | ConvertTo-Json | Set-Content -Path $eventFile
        }

        # Build the act command
        $cmd = "act"

        # Add workflow file
        $cmd += " -W `"$WorkflowFile`""
        
        # For validate-workflows.yml, explicitly specify the job ID
        if ($WorkflowFile -match "validate-workflows\.yml") {
            $cmd += " --job validate"
        }

        # Add event file
        $cmd += " -e `"$eventFile`""

        # Add job filter if provided
        if ($JobFilter) {
            $cmd += " --job `"$JobFilter`""
        }

        # Add matrix override for Python version
        Write-Host "Using Python version: $PythonVersion" -ForegroundColor Green
        $matrixFile = ".github/local-testing/matrix-input.json"
        @{
            "python-version" = $PythonVersion
        } | ConvertTo-Json | Set-Content -Path $matrixFile

        $cmd += " --input-file `"$matrixFile`""

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
        Write-Host "Running: $cmd" -ForegroundColor Green
        Invoke-Expression $cmd

        $actExit = $LASTEXITCODE
        return ($actExit -eq 0)
    }
}

# If validate only, run validation and exit
if ($ValidateOnly) {
    $validationResult = Validate-Workflow -WorkflowFile $WorkflowFile
    if (-not $validationResult) {
        exit 1
    }
    exit 0
}

# Validate the workflow file first
$validationResult = Validate-Workflow -WorkflowFile $WorkflowFile
if (-not $validationResult) {
    Write-Host "Workflow validation failed. Fix the issues before testing." -ForegroundColor Red
    exit 1
}

# Test with both Python versions if requested
if ($BothVersions) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Testing workflow with Python 3.11 and 3.12" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    # Test with Python 3.11
    $python311Result = Run-TestsWithPython -PythonVersion "3.11"

    # Test with Python 3.12
    $python312Result = Run-TestsWithPython -PythonVersion "3.12"

    # Summary
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Test Summary" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    if ($python311Result) {
        Write-Host "Python 3.11: ✅ PASSED" -ForegroundColor Green
    } else {
        Write-Host "Python 3.11: ❌ FAILED" -ForegroundColor Red
    }

    if ($python312Result) {
        Write-Host "Python 3.12: ✅ PASSED" -ForegroundColor Green
    } else {
        Write-Host "Python 3.12: ❌ FAILED" -ForegroundColor Red
    }

    Write-Host "========================================" -ForegroundColor Cyan

    # Return non-zero exit code if any test failed
    if (-not $python311Result -or -not $python312Result) {
        exit 1
    }

    exit 0
}

# Test with specific Python version if provided
if ($PythonVersion) {
    $pythonResult = Run-TestsWithPython -PythonVersion $PythonVersion
    if (-not $pythonResult) {
        exit 1
    }
    exit 0
}

# If no Python version specified, run with default settings
if ($SkipDocker) {
    Write-Host "Running tests with default Python version..." -ForegroundColor Green

    # Use hatch or poetry based on what's available
    $hatchInstalled = $null
    $poetryInstalled = $null

    try {
        $hatchInstalled = Get-Command hatch -ErrorAction SilentlyContinue
    } catch {
        $hatchInstalled = $null
    }

    try {
        $poetryInstalled = Get-Command poetry -ErrorAction SilentlyContinue
    } catch {
        $poetryInstalled = $null
    }

    if ($hatchInstalled) {
        Write-Host "Using hatch to run tests..." -ForegroundColor Green
        hatch run test
    } elseif ($poetryInstalled) {
        Write-Host "Using poetry to run tests..." -ForegroundColor Green
        poetry install
        poetry run pytest
    } else {
        Write-Host "Neither hatch nor poetry found. Using system Python..." -ForegroundColor Yellow
        python -m pytest
    }
} else {
    # Create event file if it doesn't exist
    $eventsDir = ".github/local-testing/events"
    if (-not (Test-Path $eventsDir)) {
        New-Item -Path $eventsDir -ItemType Directory -Force | Out-Null
    }

    # For validate-workflows.yml, use workflow_dispatch event
    if ($WorkflowFile -match "validate-workflows\.yml" -and (Test-Path "$eventsDir/workflow_dispatch.json")) {
        $eventFile = "$eventsDir/workflow_dispatch.json"
        $EventType = "workflow_dispatch"
    } else {
        $eventFile = "$eventsDir/$EventType.json"
    }
    
    if (-not (Test-Path $eventFile)) {
        Write-Host "Creating sample $EventType event..." -ForegroundColor Green
        @{
            "event_type" = $EventType
        } | ConvertTo-Json | Set-Content -Path $eventFile
    }

    # Build the act command
    $cmd = "act"

    # Add workflow file
    $cmd += " -W `"$WorkflowFile`""
    
    # For validate-workflows.yml, explicitly specify the job ID
    if ($WorkflowFile -match "validate-workflows\.yml") {
        $cmd += " --job validate"
    }

    # Add event file
    $cmd += " -e `"$eventFile`""

    # Add job filter if provided
    if ($JobFilter) {
        $cmd += " --job `"$JobFilter`""
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
    Write-Host "Running: $cmd" -ForegroundColor Green
    Invoke-Expression $cmd
}
