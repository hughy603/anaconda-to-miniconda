# PowerShell script to validate GitHub Actions workflow files
param(
    [Parameter(Mandatory=$true)][string]$WorkflowFile
)

if (-not $WorkflowFile) {
    Write-Host "Usage: $PSCommandPath <workflow-file>"
    Write-Host "Example: $PSCommandPath .github/workflows/ci.yml"
    exit 1
}

# Check if the workflow file exists
if (-not (Test-Path $WorkflowFile)) {
    Write-Host "Error: Workflow file not found: $WorkflowFile" -ForegroundColor Red
    exit 1
}

# Check if actionlint is installed
$actionlintInstalled = $null
try {
    $actionlintInstalled = Get-Command actionlint -ErrorAction SilentlyContinue
} catch {
    $actionlintInstalled = $null
}

if (-not $actionlintInstalled) {
    Write-Host "Warning: actionlint is not installed." -ForegroundColor Yellow

    # Try to install actionlint using winget
    $wingetInstalled = $null
    try {
        $wingetInstalled = Get-Command winget -ErrorAction SilentlyContinue
    } catch {
        $wingetInstalled = $null
    }

    if ($wingetInstalled) {
        Write-Host "Attempting to install actionlint using winget..." -ForegroundColor Yellow
        winget install rhysd.actionlint
    } else {
        Write-Host "Please install actionlint manually:" -ForegroundColor Yellow
        Write-Host "https://github.com/rhysd/actionlint#installation" -ForegroundColor Yellow

        $installChoice = Read-Host "Do you want to continue without actionlint? (y/n)"
        if ($installChoice -ne "y") {
            exit 1
        }
    }
}

# Run actionlint if available
$actionlintExitCode = 0
if (Get-Command actionlint -ErrorAction SilentlyContinue) {
    Write-Host "Validating workflow: $WorkflowFile" -ForegroundColor Cyan
    actionlint $WorkflowFile
    $actionlintExitCode = $LASTEXITCODE
} else {
    Write-Host "Skipping actionlint validation (not installed)" -ForegroundColor Yellow
}

# Additional custom checks
Write-Host "Running custom checks..." -ForegroundColor Cyan

# Check for common issues
$workflowContent = Get-Content $WorkflowFile -Raw

if ($workflowContent -match "uses: actions/checkout@master") {
    Write-Host "ERROR: Uses actions/checkout@master instead of a version tag" -ForegroundColor Red
    exit 1
}

if ($workflowContent -match "uses: actions/setup-python@master") {
    Write-Host "ERROR: Uses actions/setup-python@master instead of a version tag" -ForegroundColor Red
    exit 1
}

# Check for matrix strategy
if ($workflowContent -match "matrix:") {
    Write-Host "Matrix strategy found" -ForegroundColor Green

    # Check if Python versions are specified
    if ($workflowContent -match "python-version:") {
        Write-Host "Python versions specified in matrix" -ForegroundColor Green

        # Check if Python 3.11 and 3.12 are included
        if (-not ($workflowContent -match "3.11" -and $workflowContent -match "3.12")) {
            Write-Host "WARNING: Matrix should include Python 3.11 and 3.12" -ForegroundColor Yellow
        }
    }
}

# Check for environment variables for local testing
if (-not ($workflowContent -match "ACT_LOCAL_TESTING")) {
    Write-Host "WARNING: Workflow does not contain conditionals for local testing (ACT_LOCAL_TESTING)" -ForegroundColor Yellow
    Write-Host "Consider adding conditionals to make the workflow compatible with local testing:" -ForegroundColor Yellow
    Write-Host "Example:" -ForegroundColor Yellow
    Write-Host "  if: `${{ env.ACT_LOCAL_TESTING != 'true' }}" -ForegroundColor Yellow
    Write-Host "  or" -ForegroundColor Yellow
    Write-Host "  if [[ `"`${{ env.ACT_LOCAL_TESTING }}`" == `"true`" ]]; then" -ForegroundColor Yellow
    Write-Host "    # Simplified version for local testing" -ForegroundColor Yellow
    Write-Host "  else" -ForegroundColor Yellow
    Write-Host "    # Full version for GitHub" -ForegroundColor Yellow
    Write-Host "  fi" -ForegroundColor Yellow
}

# Check for hardcoded secrets
if ($workflowContent -match "GITHUB_TOKEN:") {
    Write-Host "WARNING: Workflow contains hardcoded GITHUB_TOKEN reference" -ForegroundColor Yellow
    Write-Host "Consider using `${{ secrets.GITHUB_TOKEN }} instead" -ForegroundColor Yellow
}

# Final status
if ($actionlintExitCode -eq 0) {
    Write-Host "Validation complete. No actionlint errors found." -ForegroundColor Green
} else {
    Write-Host "Validation complete. actionlint found errors." -ForegroundColor Red
    exit $actionlintExitCode
}
