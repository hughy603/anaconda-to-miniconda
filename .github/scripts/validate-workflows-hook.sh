#!/bin/bash
# Pre-commit hook to validate GitHub Actions workflows

set -e

# Check if actionlint is installed
if ! command -v actionlint &> /dev/null; then
    echo "Error: actionlint is not installed. Please install it first:"
    echo "https://github.com/rhysd/actionlint#installation"
    exit 1
fi

# Get the list of workflow files to check
FILES=("$@")

if [ ${#FILES[@]} -eq 0 ]; then
    echo "No workflow files to check"
    exit 0
fi

# Check each file
ERRORS=0
for file in "${FILES[@]}"; do
    echo "Validating $file..."

    # Run actionlint
    if ! actionlint "$file"; then
        ERRORS=$((ERRORS + 1))
    fi

    # Check for deprecated actions
    if grep -q "uses:.*@master" "$file"; then
        echo "Error: $file uses actions with @master tag instead of version tag"
        ERRORS=$((ERRORS + 1))
    fi

    # Check for outdated action versions
    if grep -q "uses: actions/checkout@v[1-3]" "$file"; then
        echo "Warning: $file uses outdated actions/checkout version, consider upgrading to v4"
    fi

    if grep -q "uses: actions/setup-python@v[1-4]" "$file"; then
        echo "Warning: $file uses outdated actions/setup-python version, consider upgrading to v5"
    fi

    # Check for proper environment variable usage
    if grep -q "ACT_LOCAL_TESTING" "$file" && ! grep -q "ACT_LOCAL_TESTING: \${{ vars.ACT_LOCAL_TESTING || 'false' }}" "$file"; then
        echo "Warning: $file should define ACT_LOCAL_TESTING with a default value: ACT_LOCAL_TESTING: \${{ vars.ACT_LOCAL_TESTING || 'false' }}"
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo "Found $ERRORS errors in workflow files"
    exit 1
fi

echo "All workflow files are valid"
exit 0
