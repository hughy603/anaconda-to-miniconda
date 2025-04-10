# PowerShell script to clean up redundant scripts after consolidation
# This script removes the old scripts that have been replaced by the consolidated versions

# List of files to remove
$filesToRemove = @(
    "run-act-direct.ps1",
    "run-act-mapped.ps1",
    "run-act-temp.ps1",
    "run-act-windows.bat",
    "run-act-wsl.sh",
    "run-act.bat",
    "run-act.ps1"
)

Write-Host "Cleaning up redundant scripts..." -ForegroundColor Cyan
Write-Host "The following files will be removed:" -ForegroundColor Yellow
$filesToRemove | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }

$confirmation = Read-Host "Do you want to proceed? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Cleanup cancelled." -ForegroundColor Red
    exit
}

# Remove the files
foreach ($file in $filesToRemove) {
    $filePath = Join-Path -Path $PSScriptRoot -ChildPath $file
    if (Test-Path $filePath) {
        Remove-Item -Path $filePath -Force
        Write-Host "Removed: $file" -ForegroundColor Green
    } else {
        Write-Host "File not found: $file" -ForegroundColor Yellow
    }
}

Write-Host "Cleanup completed successfully." -ForegroundColor Green
Write-Host "The following files have been kept:" -ForegroundColor Cyan
Write-Host "  - act-runner.ps1 (consolidated script)" -ForegroundColor Cyan
Write-Host "  - test-workflow.ps1 (PowerShell entry point)" -ForegroundColor Cyan
Write-Host "  - test-workflow.sh (Bash entry point)" -ForegroundColor Cyan
Write-Host "  - test-python-versions.ps1 (PowerShell Python versions script)" -ForegroundColor Cyan
Write-Host "  - test-python-versions.sh (Bash Python versions script)" -ForegroundColor Cyan
Write-Host "  - README.md (documentation)" -ForegroundColor Cyan
