# PowerShell script to test a workflow with different Python versions
param(
    [string]$WorkflowFile = ".github/workflows/ci.yml",
    [string]$EventType = "push",
    [string]$JobFilter = "",
    [switch]$SkipDocker = $false
)

# Display header
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing workflow with Python 3.11 and 3.12" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Workflow: $WorkflowFile"
Write-Host "Event: $EventType"
if ($JobFilter) {
    Write-Host "Job: $JobFilter"
}
if ($SkipDocker) {
    Write-Host "Mode: Direct (no Docker)"
}
else {
    Write-Host "Mode: Docker"
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test with Python 3.11
Write-Host "Testing with Python 3.11..." -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

if ($SkipDocker) {
    & ".github/scripts/github-actions-test.ps1" -WorkflowFile $WorkflowFile -EventType $EventType -JobFilter $JobFilter -PythonVersion "3.11" -SkipDocker
}
else {
    & ".github/scripts/github-actions-test.ps1" -WorkflowFile $WorkflowFile -EventType $EventType -JobFilter $JobFilter -PythonVersion "3.11"
}

$Python311Exit = $LASTEXITCODE
Write-Host "----------------------------------------" -ForegroundColor Green
Write-Host ""

# Test with Python 3.12
Write-Host "Testing with Python 3.12..." -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

if ($SkipDocker) {
    & ".github/scripts/github-actions-test.ps1" -WorkflowFile $WorkflowFile -EventType $EventType -JobFilter $JobFilter -PythonVersion "3.12" -SkipDocker
}
else {
    & ".github/scripts/github-actions-test.ps1" -WorkflowFile $WorkflowFile -EventType $EventType -JobFilter $JobFilter -PythonVersion "3.12"
}

$Python312Exit = $LASTEXITCODE
Write-Host "----------------------------------------" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
if ($Python311Exit -eq 0) {
    Write-Host "Python 3.11: ✅ PASSED" -ForegroundColor Green
}
else {
    Write-Host "Python 3.11: ❌ FAILED" -ForegroundColor Red
}

if ($Python312Exit -eq 0) {
    Write-Host "Python 3.12: ✅ PASSED" -ForegroundColor Green
}
else {
    Write-Host "Python 3.12: ❌ FAILED" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan

# Return non-zero exit code if any test failed
if ($Python311Exit -ne 0 -or $Python312Exit -ne 0) {
    exit 1
}
