# PowerShell wrapper for test-python-versions.sh
param(
    [Parameter(Mandatory=$true)][string]$WorkflowFile,
    [string]$EventType = "push"
)

# Ensure paths use forward slashes
$WorkflowFile = $WorkflowFile.Replace("\", "/")

# Call the bash script
bash .github/local-testing/test-python-versions.sh $WorkflowFile $EventType
