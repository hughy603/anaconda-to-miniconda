#!/bin/bash
# Pre-commit hook to check workflow references

set -e

# Get the list of workflow files to check
FILES=("$@")

if [ ${#FILES[@]} -eq 0 ]; then
    echo "No workflow files to check"
    exit 0
fi

# Get all available composite actions
AVAILABLE_ACTIONS=$(find .github/actions -name "action.yml" -o -name "action.yaml" | sed 's|.github/actions/||g' | sed 's|/action.yml||g' | sed 's|/action.yaml||g')

# Check each file
ERRORS=0
for file in "${FILES[@]}"; do
    echo "Checking references in $file..."

    # Extract all action references
    REFERENCES=$(grep -o "uses: \../.github/actions/[a-zA-Z0-9_-]*" "$file" 2>/dev/null | sed 's|uses: \../.github/actions/||g' || true)

    if [ -z "$REFERENCES" ]; then
        echo "No composite action references found in $file"
        continue
    fi

    # Check each reference
    for ref in $REFERENCES; do
        if ! echo "$AVAILABLE_ACTIONS" | grep -q "$ref"; then
            echo "Error: $file references non-existent action: $ref"
            ERRORS=$((ERRORS + 1))
        fi
    done

    # Check for proper reference format
    if grep -q "uses: .github/actions/" "$file"; then
        echo "Error: $file uses incorrect action reference format. Use './.github/actions/' instead of '.github/actions/'"
        ERRORS=$((ERRORS + 1))
    fi

    # Check for workflow calls
    WORKFLOW_CALLS=$(grep -o "uses: \../.github/workflows/[a-zA-Z0-9_-]*" "$file" 2>/dev/null | sed 's|uses: \../.github/workflows/||g' || true)

    if [ -n "$WORKFLOW_CALLS" ]; then
        for workflow in $WORKFLOW_CALLS; do
            if [ ! -f ".github/workflows/$workflow" ]; then
                echo "Error: $file calls non-existent workflow: $workflow"
                ERRORS=$((ERRORS + 1))
            fi
        done
    fi

    # Check for environment variables
    if grep -q "ACT_LOCAL_TESTING" "$file"; then
        if ! grep -q "env:" "$file"; then
            echo "Warning: $file uses ACT_LOCAL_TESTING but doesn't define it in the env section"
        fi
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo "Found $ERRORS errors in workflow references"
    exit 1
fi

echo "All workflow references are valid"
exit 0
