#!/bin/bash
# Script to update the pre-commit configuration to include Python compatibility check

PRE_COMMIT_CONFIG=".pre-commit-config.yaml"

# Check if the pre-commit config file exists
if [ ! -f "$PRE_COMMIT_CONFIG" ]; then
  echo "Error: Pre-commit config file not found: $PRE_COMMIT_CONFIG"
  exit 1
fi

# Create a backup of the original file
cp "$PRE_COMMIT_CONFIG" "$PRE_COMMIT_CONFIG.bak"
echo "Created backup: $PRE_COMMIT_CONFIG.bak"

# Check if the Python compatibility check is already in the config
if grep -q "python-version-check" "$PRE_COMMIT_CONFIG"; then
  echo "Python compatibility check already exists in the pre-commit config."
  exit 0
fi

# Add the Python compatibility check to the local hooks section
echo "Adding Python compatibility check to pre-commit config..."

# Check if local hooks section exists
if grep -q "repo: local" "$PRE_COMMIT_CONFIG"; then
  # Append to existing local hooks section
  sed -i '/repo: local/,/hooks:/a\      - id: python-version-check\n        name: Python 3.11/3.12 Compatibility Check\n        entry: python .github/scripts/check_python_compatibility.py\n        language: python\n        pass_filenames: false\n        stages: [push, manual]\n        verbose: true' "$PRE_COMMIT_CONFIG"
else
  # Add new local hooks section
  cat >> "$PRE_COMMIT_CONFIG" << 'EOF'

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
EOF
fi

echo "Pre-commit config updated successfully!"
echo "You can now run: pre-commit run python-version-check"
