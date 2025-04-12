#!/bin/bash
# Script to check GitHub Actions workflow files for shellcheck issues

# Set strict error handling
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking GitHub Actions workflows for shellcheck issues...${NC}"

# Directory containing workflow files
WORKFLOWS_DIR=".github/workflows"

# Temporary directory for extracted shell scripts
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Find all workflow files
WORKFLOW_FILES=$(find "$WORKFLOWS_DIR" -name "*.yml" -o -name "*.yaml")

# Counter for issues found
ISSUES_FOUND=0

# Process each workflow file
for file in $WORKFLOW_FILES; do
  echo -e "${YELLOW}Checking $file...${NC}"

  # Extract shell scripts from run: sections
  grep -n "run: |" "$file" | while read -r line; do
    line_num=$(echo "$line" | cut -d':' -f1)
    script_start=$((line_num + 1))

    # Extract the script content
    script_content=$(sed -n "${script_start},/^[[:space:]]*[^[:space:]]/p" "$file" | sed '/^[[:space:]]*[^[:space:]]/d')

    if [ -n "$script_content" ]; then
      # Save to temporary file
      temp_script="$TEMP_DIR/$(basename "$file")_line_${line_num}.sh"
      echo "$script_content" > "$temp_script"

      # Run shellcheck with specific focus on SC2086 (unquoted variables)
      shellcheck_output=$(shellcheck -s bash -S warning "$temp_script" 2>&1 || true)

      # Check specifically for SC2086 errors
      if echo "$shellcheck_output" | grep -q "SC2086"; then
        echo -e "${RED}SC2086 error found in $file at line $line_num:${NC}"
        echo -e "${RED}$shellcheck_output${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
      fi
    fi
  done
done

# Report results
if [ "$ISSUES_FOUND" -eq 0 ]; then
  echo -e "${GREEN}No SC2086 issues found in workflow files.${NC}"
  exit 0
else
  echo -e "${RED}Found $ISSUES_FOUND SC2086 issues in workflow files.${NC}"
  echo -e "${YELLOW}Fix by adding double quotes around variables, e.g., change 'echo value >> \$GITHUB_OUTPUT' to 'echo value >> \"\$GITHUB_OUTPUT\"'${NC}"
  exit 1
fi
