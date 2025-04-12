#!/bin/bash
# Pre-commit hook to validate GitHub Actions composite actions

set -e

# Check if python is installed
if ! command -v python &> /dev/null; then
    echo "Error: python is not installed. Please install it first."
    exit 1
fi

# Get the list of action files to check
FILES=("$@")

if [ ${#FILES[@]} -eq 0 ]; then
    echo "No action files to check"
    exit 0
fi

# Check each file
ERRORS=0
for file in "${FILES[@]}"; do
    echo "Validating $file..."

    # Validate YAML syntax
    if ! python -c "import yaml; yaml.safe_load(open('$file'))"; then
        echo "Error: Invalid YAML in $file"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Check for required fields
    if ! python -c "
import yaml
action = yaml.safe_load(open('$file'))
assert 'name' in action, 'Missing name field'
assert 'description' in action, 'Missing description field'
assert 'runs' in action, 'Missing runs field'
assert 'using' in action['runs'], 'Missing using field in runs'
if action['runs']['using'] == 'composite':
    assert 'steps' in action['runs'], 'Missing steps field in runs'
"; then
        echo "Error: Missing required fields in $file"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Check for proper inputs documentation
    if ! python -c "
import yaml
action = yaml.safe_load(open('$file'))
if 'inputs' in action:
    for input_name, input_data in action['inputs'].items():
        assert 'description' in input_data, f'Input {input_name} is missing description'
        if 'required' not in input_data:
            print(f'Warning: Input {input_name} should specify if it is required')
"; then
        echo "Error: Inputs not properly documented in $file"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Check for shell specification in composite steps
    if ! python -c "
import yaml
action = yaml.safe_load(open('$file'))
if action['runs']['using'] == 'composite':
    for step in action['runs']['steps']:
        if 'run' in step:
            assert 'shell' in step, f'Step \"{step.get(\"name\", \"unnamed\")}\" with run command is missing shell specification'
"; then
        echo "Error: Steps with run commands must specify shell in $file"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    echo "✓ $file is valid"
done

if [ $ERRORS -gt 0 ]; then
    echo "Found $ERRORS errors in action files"
    exit 1
fi

echo "All action files are valid"
exit 0
