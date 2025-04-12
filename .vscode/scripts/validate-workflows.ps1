# File: .vscode/scripts/validate-workflows.ps1
param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath
)

# Only run on workflow files
if ($FilePath -like ".github/workflows/*" -or $FilePath -like ".github/actions/*/action.yml") {
    # Run pre-commit on the specific file
    pre-commit run actionlint --files "$FilePath"
}
else {
    Write-Output "Not a GitHub Actions workflow file, skipping validation."
    exit 0
}
