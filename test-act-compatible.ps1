# PowerShell script to demonstrate local testing of act-compatible GitHub Actions workflows

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
Write-Host "Act-Compatible Workflow Testing Demo" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Test the sample workflow
Write-Host "Testing sample-local-testing.yml workflow..." -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Green
act -W .github/workflows/sample-local-testing.yml -e .github/local-testing/events/push.json
Write-Host ""

# Test the CI workflow
Write-Host "Testing ci.yml workflow..." -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Green
act -W .github/workflows/ci.yml -e .github/local-testing/events/push.json --env ACT_LOCAL_TESTING=true
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Act-compatible testing demo completed!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "For local testing, workflows should:" -ForegroundColor Yellow
Write-Host "1. Use the ACT_LOCAL_TESTING environment variable to adapt behavior" -ForegroundColor Yellow
Write-Host "2. Simplify matrix configurations when running locally" -ForegroundColor Yellow
Write-Host "3. Skip steps that won't work in local testing" -ForegroundColor Yellow
Write-Host ""
Write-Host "For more options, see the documentation in github-actions-guide.md" -ForegroundColor Yellow
