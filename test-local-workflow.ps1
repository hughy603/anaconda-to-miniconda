# PowerShell script to demonstrate local testing of GitHub Actions workflows

# Ensure we're in the project root directory
Set-Location -Path $PSScriptRoot

# Check if act is installed
$actInstalled = $null
try {
    $actInstalled = Get-Command act -ErrorAction SilentlyContinue
} catch {
    $actInstalled = $null
}

if (-not $actInstalled) {
    Write-Host "Error: act is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "https://github.com/nektos/act#installation" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: Docker is not installed or not in PATH. Please install Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Display header
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "GitHub Actions Local Testing Demo" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test the sample workflow
Write-Host "Testing sample-local-testing.yml workflow..." -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Green
& ".github/local-testing/local-test.ps1" -WorkflowFile ".github/workflows/sample-local-testing.yml"
Write-Host ""

# Test the CI workflow with Python 3.11
Write-Host "Testing CI workflow with Python 3.11..." -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Green
& ".github/local-testing/local-test.ps1" -WorkflowFile ".github/workflows/ci.yml" -PythonVersion "3.11"
Write-Host ""

# Validate a workflow
Write-Host "Validating sample workflow..." -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Green
& ".github/local-testing/validate-workflow.ps1" -WorkflowFile ".github/workflows/sample-local-testing.yml"
Write-Host ""

# Validate CI workflow
Write-Host "Validating CI workflow..." -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Green
& ".github/local-testing/validate-workflow.ps1" -WorkflowFile ".github/workflows/ci.yml"
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Local testing demo completed!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more options, see the documentation in github-actions-guide.md" -ForegroundColor Yellow
