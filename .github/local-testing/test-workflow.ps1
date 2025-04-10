# PowerShell wrapper for test-workflow.sh
param(
    [Parameter(Mandatory=$true)][string]$WorkflowFile,
    [string]$EventType = "push",
    [string]$MatrixOverride = ""
)

# Ensure paths use forward slashes
$WorkflowFile = $WorkflowFile.Replace("\", "/")

# Call the bash script
if ($MatrixOverride -eq "") {
    bash .github/local-testing/test-workflow.sh $WorkflowFile $EventType
} else {
    bash .github/local-testing/test-workflow.sh $WorkflowFile $EventType $MatrixOverride
}
