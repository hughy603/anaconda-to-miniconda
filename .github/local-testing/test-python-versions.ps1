# PowerShell script to test GitHub Actions workflows with different Python versions
param(
    [Parameter(Mandatory=$true)][string]$WorkflowFile,
    [string]$EventType = "push",
    [string]$Platform = "ubuntu-latest",
    [string]$DockerImage = "ghcr.io/catthehacker/ubuntu:act-latest",
    [switch]$DryRun = $false
)

Write-Host "Testing workflow with Python 3.11..." -ForegroundColor Cyan
# Create a temporary JSON file for matrix inputs
$matrixJson = @{
    "python-version" = "3.11"
} | ConvertTo-Json

$matrixFile = ".github/local-testing/matrix-python311.json"
Set-Content -Path $matrixFile -Value $matrixJson

# Run act for Python 3.11
$eventFile = ".github/local-testing/events/$EventType.json"
& "$PSScriptRoot\act-runner.ps1" -WorkflowFile $WorkflowFile -EventFile $eventFile -MatrixFile $matrixFile -Platform $Platform -DockerImage $DockerImage -DryRun:$DryRun

Write-Host "`nTesting workflow with Python 3.12..." -ForegroundColor Cyan
# Create a temporary JSON file for matrix inputs
$matrixJson = @{
    "python-version" = "3.12"
} | ConvertTo-Json

$matrixFile = ".github/local-testing/matrix-python312.json"
Set-Content -Path $matrixFile -Value $matrixJson

# Run act for Python 3.12
& "$PSScriptRoot\act-runner.ps1" -WorkflowFile $WorkflowFile -EventFile $eventFile -MatrixFile $matrixFile -Platform $Platform -DockerImage $DockerImage -DryRun:$DryRun
