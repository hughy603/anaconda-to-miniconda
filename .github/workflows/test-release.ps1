# Set environment variables for local testing
$env:ACT_LOCAL_TESTING = "true"
$env:PYTHON_VERSION = "3.11"
$env:UV_VERSION = "0.6.14"

# Check for GitHub token
if (-not $env:GITHUB_TOKEN) {
    Write-Host "❌ GITHUB_TOKEN environment variable not set" -ForegroundColor Red
    Write-Host "Please set your GitHub Personal Access Token (PAT) for local testing:" -ForegroundColor Yellow
    Write-Host "1. Go to GitHub.com -> Settings -> Developer Settings -> Personal Access Tokens" -ForegroundColor Yellow
    Write-Host "2. Generate a new token with 'repo' and 'workflow' scopes" -ForegroundColor Yellow
    Write-Host "3. Set the token: `$env:GITHUB_TOKEN = 'your_token_here'" -ForegroundColor Yellow
    exit 1
}

# Mock PyPI token for local testing
$env:PYPI_API_TOKEN = "dummy_token"

# Create event file if it doesn't exist
$EventFile = ".github/events/workflow_dispatch.json"
if (-not (Test-Path $EventFile)) {
    $EventDir = Split-Path $EventFile
    if (-not (Test-Path $EventDir)) {
        New-Item -ItemType Directory -Path $EventDir | Out-Null
    }
    @"
{
    "inputs": {
        "require_approval": "false"
    }
}
"@ | Set-Content $EventFile
}

# Get the absolute path to the workspace
$WorkspacePath = (Get-Location).Path

# Clean up any existing act cache
Write-Host "🧹 Cleaning up act cache..." -ForegroundColor Cyan
Remove-Item -Path "$env:USERPROFILE\.cache\act" -Recurse -Force -ErrorAction SilentlyContinue

# Run the release workflow with proper workspace binding
Write-Host "🚀 Running release workflow test..." -ForegroundColor Cyan
act workflow_dispatch `
    -e $EventFile `
    -W .github/workflows/release.yml `
    --container-architecture linux/amd64 `
    --secret GITHUB_TOKEN=$env:GITHUB_TOKEN `
    --bind `
    --env ACT_LOCAL_TESTING=true `
    --env PYTHON_VERSION=$env:PYTHON_VERSION `
    --env UV_VERSION=$env:UV_VERSION `
    -v `
    --rm

# Check if the workflow completed successfully
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Release workflow test completed successfully" -ForegroundColor Green
}
else {
    Write-Host "❌ Release workflow test failed" -ForegroundColor Red
    Write-Host "Check the output above for errors" -ForegroundColor Yellow
    exit 1
}