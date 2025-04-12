# PowerShell script to update the CI workflow file with conditional execution for local testing

$CIWorkflow = ".github/workflows/ci.yml"

# Check if the workflow file exists
if (-not (Test-Path $CIWorkflow)) {
    Write-Host "Error: CI workflow file not found: $CIWorkflow" -ForegroundColor Red
    exit 1
}

# Create a backup of the original file
Copy-Item -Path $CIWorkflow -Destination "$CIWorkflow.bak"
Write-Host "Created backup: $CIWorkflow.bak" -ForegroundColor Green

# Read the workflow file content
$content = Get-Content -Path $CIWorkflow -Raw

# Add ACT_LOCAL_TESTING environment variable if it doesn't exist
if ($content -notmatch "ACT_LOCAL_TESTING") {
    Write-Host "Adding ACT_LOCAL_TESTING environment variable..." -ForegroundColor Green

    # Find the env section and add the variable
    $content = $content -replace "env:([\s\S]*?)\n", "env:$1`n  ACT_LOCAL_TESTING: `${{ vars.ACT_LOCAL_TESTING || 'false' }}`n"
}

# Update matrix configuration for conditional execution
Write-Host "Updating matrix configuration for conditional execution..." -ForegroundColor Green

# Update python-version matrix
$content = $content -replace 'python-version: \["3.11", "3.12"\]', 'python-version: ${{ env.ACT_LOCAL_TESTING == ''true'' && fromJSON(''["3.11"]'') || fromJSON(''["3.11", "3.12"]'') }}'

# Update os matrix
$content = $content -replace 'os: \["ubuntu-latest", "windows-latest", "macos-latest"\]', 'os: ${{ env.ACT_LOCAL_TESTING == ''true'' && fromJSON(''["ubuntu-latest"]'') || fromJSON(''["ubuntu-latest", "windows-latest", "macos-latest"]'') }}'

# Add conditional execution for steps that shouldn't run locally
Write-Host "Adding conditional execution for steps that shouldn't run locally..." -ForegroundColor Green

# Find the Upload coverage to Codecov step and add conditional
$content = $content -replace 'if: matrix.os == ''ubuntu-latest''(\s+)uses: codecov/codecov-action', 'if: matrix.os == ''ubuntu-latest'' && env.ACT_LOCAL_TESTING != ''true''$1uses: codecov/codecov-action'

# Find the Run security checks step and add conditional
$content = $content -replace 'if: matrix.os == ''ubuntu-latest'' && matrix.python-version == ''3.11''(\s+)run:', 'if: matrix.os == ''ubuntu-latest'' && matrix.python-version == ''3.11'' && env.ACT_LOCAL_TESTING != ''true''$1run:'

# Write the updated content back to the file
Set-Content -Path $CIWorkflow -Value $content

Write-Host "CI workflow file updated successfully!" -ForegroundColor Green
Write-Host "You can now test it with: .github/scripts/test-github-actions.ps1" -ForegroundColor Green
