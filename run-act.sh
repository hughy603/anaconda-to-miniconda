#!/bin/bash

# Simple script to run act with custom images
# Usage: ./run-act.sh [workflow_file] [job_name] [event_type]

# Default values
WORKFLOW_FILE=${1:-".github/workflows/ci.yml"}
JOB_NAME=${2:-""}
EVENT_TYPE=${3:-"push"}

# Function to install act if not present
install_act() {
    if ! command -v act &> /dev/null; then
        echo "act not found. Installing..."

        # Check OS and install appropriate package manager if needed
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            if command -v apt-get &> /dev/null; then
                # Debian/Ubuntu
                curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
            elif command -v dnf &> /dev/null; then
                # Fedora
                sudo dnf install act
            elif command -v pacman &> /dev/null; then
                # Arch Linux
                sudo pacman -S act
            else
                echo "Unsupported Linux distribution. Please install act manually."
                exit 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install act
            else
                echo "Homebrew not found. Please install Homebrew first."
                exit 1
            fi
        else
            echo "Unsupported operating system. Please install act manually."
            exit 1
        fi
    fi
}

# Error checking
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "Error: Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi

EVENT_FILE=".github/events/templates/$EVENT_TYPE.json"
if [ ! -f "$EVENT_FILE" ]; then
    echo "Error: Event file not found: $EVENT_FILE"
    echo "Available event types: push, pull_request"
    exit 1
fi

# Install act if needed
install_act

# Custom images configuration
CUSTOM_IMAGES=(
    "ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"
    "ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04"
    "ubuntu-20.04=ghcr.io/catthehacker/ubuntu:act-20.04"
)

# Build the act command
ACT_CMD="act"

# Add custom images
for image in "${CUSTOM_IMAGES[@]}"; do
    ACT_CMD="$ACT_CMD --container-architecture linux/amd64 --image $image"
done

# Add workflow file
ACT_CMD="$ACT_CMD -W $WORKFLOW_FILE"

# Add job if specified
if [ -n "$JOB_NAME" ]; then
    ACT_CMD="$ACT_CMD -j $JOB_NAME"
fi

# Add event type
ACT_CMD="$ACT_CMD -e $EVENT_FILE"

# Add common options
ACT_CMD="$ACT_CMD --bind --rm"

# Print and run the command
echo "Running: $ACT_CMD"
eval "$ACT_CMD"
