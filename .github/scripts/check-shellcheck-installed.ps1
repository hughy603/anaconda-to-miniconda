# PowerShell script to check if shellcheck is installed

# Function to check if a command exists
function Test-CommandExists {
    param ($command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $command) { return $true }
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

# Check if shellcheck is in PATH
if (Test-CommandExists "shellcheck") {
    Write-Host "shellcheck is installed."
    exit 0
}

# Check common installation locations on Windows
$scoopPath = "$env:USERPROFILE\scoop\shims\shellcheck.exe"
$chocolateyPath = "C:\ProgramData\chocolatey\bin\shellcheck.exe"

if (Test-Path $scoopPath) {
    Write-Host "shellcheck is installed via scoop but not in PATH."
    Write-Host "Please restart your terminal or add it to PATH."
    exit 1
}

if (Test-Path $chocolateyPath) {
    Write-Host "shellcheck is installed via chocolatey but not in PATH."
    Write-Host "Please restart your terminal or add it to PATH."
    exit 1
}

# Not found
Write-Host "ERROR: shellcheck is not installed." -ForegroundColor Red
Write-Host "Please install it:"
Write-Host "  - Windows: scoop install shellcheck"
Write-Host "  - Windows (alternative): choco install shellcheck"
Write-Host "  - macOS: brew install shellcheck"
Write-Host "  - Ubuntu/Debian: apt-get install shellcheck"
Write-Host "  - Fedora/RHEL: dnf install ShellCheck"
exit 1