# PowerShell script to validate GitHub Actions workflow files
param(
    [string]$WorkflowFile = ".github/workflows/ci.yml"
)

if (-not (Test-Path $WorkflowFile)) {
    Write-Host "Error: Workflow file not found: $WorkflowFile" -ForegroundColor Red
    Write-Host "Usage: $PSCommandPath [workflow-file]"
    exit 1
}

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
    }
} else {
    Write-Host "Warning: actionlint not found. Install with: 'go install github.com/rhysd/actionlint/cmd/actionlint@latest'" -ForegroundColor Yellow
    Write-Host "Continuing with basic checks..." -ForegroundColor Yellow
}

Write-Host "Running custom checks..." -ForegroundColor Green

# Check for Python version matrix
$workflowContent = Get-Content -Path $WorkflowFile -Raw
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
if ($workflowContent -notmatch "ACT_LOCAL_TESTING") {
    Write-Host "WARNING: Workflow does not have conditional execution for local testing" -ForegroundColor Yellow
    Write-Host "Consider adding: if: `${{ env.ACT_LOCAL_TESTING != 'true' }} for steps that shouldn't run locally" -ForegroundColor Yellow
}

# Check for deprecated actions
if ($workflowContent -match "uses: actions/[^@]*@master") {
    Write-Host "ERROR: Uses actions with @master tag instead of version tag" -ForegroundColor Red
    Write-Host "Replace @master with specific version tags like @v4" -ForegroundColor Yellow
}

# Check for hardcoded Python versions
if ($workflowContent -match "python-version: [""']3\.[0-9][0-9]*[""']") {
    Write-Host "WARNING: Hardcoded Python version found. Consider using matrix or environment variables." -ForegroundColor Yellow
}

# Check for proper environment variable usage
if ($workflowContent -notmatch "env:") {
    Write-Host "TIP: Consider using environment variables for common values" -ForegroundColor Cyan
}

# Check for proper cache usage
if ($workflowContent -match "actions/cache" -and $workflowContent -notmatch "actions/cache@v4") {
    Write-Host "WARNING: Using outdated version of actions/cache. Consider upgrading to v4." -ForegroundColor Yellow
}

Write-Host "Validation complete" -ForegroundColor Green

# Return non-zero exit code if actionlint failed
if ($actionlintExit -ne 0) {
    exit $actionlintExit
}
