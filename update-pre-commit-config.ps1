# PowerShell script to update the pre-commit configuration to include Python compatibility check

$PreCommitConfig = ".pre-commit-config.yaml"

# Check if the pre-commit config file exists
if (-not (Test-Path $PreCommitConfig)) {
    Write-Host "Error: Pre-commit config file not found: $PreCommitConfig" -ForegroundColor Red
    exit 1
}

# Create a backup of the original file
Copy-Item -Path $PreCommitConfig -Destination "$PreCommitConfig.bak"
Write-Host "Created backup: $PreCommitConfig.bak" -ForegroundColor Green

# Read the pre-commit config file
$content = Get-Content -Path $PreCommitConfig -Raw

# Check if the Python compatibility check is already in the config
if ($content -match "python-version-check") {
    Write-Host "Python compatibility check already exists in the pre-commit config." -ForegroundColor Yellow
    exit 0
}

# Add the Python compatibility check to the local hooks section
Write-Host "Adding Python compatibility check to pre-commit config..." -ForegroundColor Green

# Check if local hooks section exists
if ($content -match "repo: local") {
    # Append to existing local hooks section
    $localRepoPattern = "(repo: local[\s\S]*?hooks:[\s\S]*?)(  - repo:|\Z)"
    $localRepoMatch = [regex]::Match($content, $localRepoPattern)

    if ($localRepoMatch.Success) {
        $localRepoContent = $localRepoMatch.Groups[1].Value
        $afterLocalRepo = $localRepoMatch.Groups[2].Value

        $newLocalRepoContent = $localRepoContent + @"
      - id: python-version-check
        name: Python 3.11/3.12 Compatibility Check
        entry: python .github/scripts/check_python_compatibility.py
        language: python
        pass_filenames: false
        stages: [push, manual]
        verbose: true

"@ + $afterLocalRepo

        $content = $content.Replace($localRepoMatch.Value, $newLocalRepoContent)
    } else {
        Write-Host "Could not find the hooks section in the local repo. Adding new section." -ForegroundColor Yellow
        $content += @"

  # Python compatibility check
  - repo: local
    hooks:
      - id: python-version-check
        name: Python 3.11/3.12 Compatibility Check
        entry: python .github/scripts/check_python_compatibility.py
        language: python
        pass_filenames: false
        stages: [push, manual]
        verbose: true
"@
    }
} else {
    # Add new local hooks section
    $content += @"

  # Python compatibility check
  - repo: local
    hooks:
      - id: python-version-check
        name: Python 3.11/3.12 Compatibility Check
        entry: python .github/scripts/check_python_compatibility.py
        language: python
        pass_filenames: false
        stages: [push, manual]
        verbose: true
"@
}

# Write the updated content back to the file
Set-Content -Path $PreCommitConfig -Value $content

Write-Host "Pre-commit config updated successfully!" -ForegroundColor Green
Write-Host "You can now run: pre-commit run python-version-check" -ForegroundColor Green
