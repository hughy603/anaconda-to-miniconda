#!/bin/bash
# Script to check if shellcheck is installed

# Check for shellcheck in PATH
if command -v shellcheck &> /dev/null; then
    echo "shellcheck is installed."
    exit 0
fi

# On Windows, check common installation locations
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    # Check scoop installation
    if [ -f "$HOME/scoop/shims/shellcheck.exe" ]; then
        echo "shellcheck is installed via scoop but not in PATH."
        echo "Please restart your terminal or add it to PATH."
        exit 1
    fi
    
    # Check chocolatey installation
    if [ -f "/c/ProgramData/chocolatey/bin/shellcheck.exe" ]; then
        echo "shellcheck is installed via chocolatey but not in PATH."
        echo "Please restart your terminal or add it to PATH."
        exit 1
    fi
fi

# Not found
echo "ERROR: shellcheck is not installed."
echo "Please install it:"
echo "  - Windows: scoop install shellcheck"
echo "  - macOS: brew install shellcheck"
echo "  - Ubuntu/Debian: apt-get install shellcheck"
echo "  - Fedora/RHEL: dnf install ShellCheck"
exit 1