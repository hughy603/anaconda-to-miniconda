# PowerShell script to test a workflow with different Python versions
param(
    [Parameter(Mandatory=$true)][string]$WorkflowFile,
    [string]$EventType = "push",
    [string]$JobFilter = "",
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$AdditionalArgs
)

if (-not $WorkflowFile) {
    Write-Host "Usage: $PSCommandPath <workflow-file> [event-type] [job-filter] [additional-args]"
    Write-Host "Examples:"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml pull_request"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml test"
    Write-Host "  $PSCommandPath .github/workflows/ci.yml push test --verbose"
    exit 1
}

Write-Host "Testing workflow with Python 3.11..." -ForegroundColor Cyan
$additionalArgsStr = if ($AdditionalArgs) { $AdditionalArgs -join ' ' } else { "" }
& "$PSScriptRoot\local-test.ps1" -WorkflowFile $WorkflowFile -EventType $EventType -JobFilter $JobFilter -MatrixOverride "python-version=3.11" $AdditionalArgs

Write-Host "`nTesting workflow with Python 3.12..." -ForegroundColor Cyan
& "$PSScriptRoot\local-test.ps1" -WorkflowFile $WorkflowFile -EventType $EventType -JobFilter $JobFilter -MatrixOverride "python-version=3.12" $AdditionalArgs
