#!/bin/bash
# Script to set up GitHub Actions workflows for a project
# This script helps configure and customize workflows based on project type

# Default values
PROJECT_TYPE="python"
PYTHON_VERSION="3.11"
USE_UV=true
USE_HATCH=true
ENABLE_COVERAGE=true
ENABLE_SECURITY=true
ENABLE_DOCS=false
FORCE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-type)
      PROJECT_TYPE="$2"
      shift 2
      ;;
    --python-version)
      PYTHON_VERSION="$2"
      shift 2
      ;;
    --use-uv)
      USE_UV=true
      shift
      ;;
    --no-uv)
      USE_UV=false
      shift
      ;;
    --use-hatch)
      USE_HATCH=true
      shift
      ;;
    --no-hatch)
      USE_HATCH=false
      shift
      ;;
    --enable-coverage)
      ENABLE_COVERAGE=true
      shift
      ;;
    --disable-coverage)
      ENABLE_COVERAGE=false
      shift
      ;;
    --enable-security)
      ENABLE_SECURITY=true
      shift
      ;;
    --disable-security)
      ENABLE_SECURITY=false
      shift
      ;;
    --enable-docs)
      ENABLE_DOCS=true
      shift
      ;;
    --disable-docs)
      ENABLE_DOCS=false
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --help)
      echo "Usage: .github/setup-workflows.sh [options]"
      echo "Options:"
      echo "  --project-type <type>    Project type (python, node, etc.) (default: python)"
      echo "  --python-version <ver>   Python version (default: 3.11)"
      echo "  --use-uv                 Use UV for dependency management (default: true)"
      echo "  --no-uv                  Don't use UV"
      echo "  --use-hatch              Use Hatch for project management (default: true)"
      echo "  --no-hatch               Don't use Hatch"
      echo "  --enable-coverage        Enable code coverage (default: true)"
      echo "  --disable-coverage       Disable code coverage"
      echo "  --enable-security        Enable security checks (default: true)"
      echo "  --disable-security       Disable security checks"
      echo "  --enable-docs            Enable documentation workflow (default: false)"
      echo "  --disable-docs           Disable documentation workflow"
      echo "  --force                  Overwrite existing files (default: false)"
      echo "  --help                   Display this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Ensure we're in the project root directory
PROJECT_ROOT=$(pwd)

# Check if .github directory exists
if [ ! -d "$PROJECT_ROOT/.github" ]; then
  echo "Creating .github directory..."
  mkdir -p "$PROJECT_ROOT/.github"
fi

# Check if .github/workflows directory exists
if [ ! -d "$PROJECT_ROOT/.github/workflows" ]; then
  echo "Creating .github/workflows directory..."
  mkdir -p "$PROJECT_ROOT/.github/workflows"
fi

# Check if .github/actions directory exists
if [ ! -d "$PROJECT_ROOT/.github/actions" ]; then
  echo "Creating .github/actions directory..."
  mkdir -p "$PROJECT_ROOT/.github/actions"
fi

# Function to copy and customize a file
copy_and_customize() {
  local source_path="$1"
  local dest_path="$2"
  local replacements="$3"

  if [ -f "$dest_path" ] && [ "$FORCE" != "true" ]; then
    echo "File already exists: $dest_path"
    echo "Use --force to overwrite"
    return 1
  fi

  if [ ! -f "$source_path" ]; then
    echo "Source file not found: $source_path"
    return 1
  fi

  # Create the destination directory if it doesn't exist
  local dest_dir=$(dirname "$dest_path")
  if [ ! -d "$dest_dir" ]; then
    mkdir -p "$dest_dir"
  fi

  # Copy the file
  cp "$source_path" "$dest_path"

  # Apply replacements
  for replacement in $replacements; do
    local key=$(echo $replacement | cut -d= -f1)
    local value=$(echo $replacement | cut -d= -f2-)
    sed -i "s|$key|$value|g" "$dest_path"
  done

  echo "Created: $dest_path"
  return 0
}

# Function to copy a directory recursively
copy_directory_recursive() {
  local source_dir="$1"
  local dest_dir="$2"
  local replacements="$3"

  if [ ! -d "$source_dir" ]; then
    echo "Source directory not found: $source_dir"
    return 1
  fi

  # Create the destination directory if it doesn't exist
  if [ ! -d "$dest_dir" ]; then
    mkdir -p "$dest_dir"
  fi

  # Copy all files in the source directory
  for file in "$source_dir"/*; do
    if [ -f "$file" ]; then
      local dest_path="$dest_dir/$(basename "$file")"
      copy_and_customize "$file" "$dest_path" "$replacements"
    fi
  done

  # Recursively copy subdirectories
  for dir in "$source_dir"/*; do
    if [ -d "$dir" ]; then
      local dest_subdir="$dest_dir/$(basename "$dir")"
      copy_directory_recursive "$dir" "$dest_subdir" "$replacements"
    fi
  done

  return 0
}

# Get project name from directory
PROJECT_NAME=$(basename "$PROJECT_ROOT")

# Create replacements string
REPLACEMENTS="PYTHON_VERSION:\ \"3.11\"=PYTHON_VERSION:\ \"$PYTHON_VERSION\" PROJECT_NAME=$PROJECT_NAME"

# Copy workflow configuration
echo "Setting up workflow configuration..."
copy_and_customize "$PROJECT_ROOT/.github/workflow-config.yml" "$PROJECT_ROOT/.github/workflow-config.yml" "$REPLACEMENTS"

# Copy workflow templates based on project type
echo "Setting up workflow templates for $PROJECT_TYPE..."
TEMPLATE_DIR="$PROJECT_ROOT/.github/templates/$PROJECT_TYPE"
if [ -d "$TEMPLATE_DIR" ]; then
  # Copy CI workflow
  copy_and_customize "$TEMPLATE_DIR/ci.yml" "$PROJECT_ROOT/.github/workflows/ci.yml" "$REPLACEMENTS"

  # Copy other workflows if needed
  if [ "$ENABLE_DOCS" = "true" ]; then
    if [ -f "$TEMPLATE_DIR/docs.yml" ]; then
      copy_and_customize "$TEMPLATE_DIR/docs.yml" "$PROJECT_ROOT/.github/workflows/docs.yml" "$REPLACEMENTS"
    fi
  fi
else
  echo "Template directory not found: $TEMPLATE_DIR"
  echo "Please ensure the template directory exists for the specified project type"
  exit 1
fi

# Copy composite actions
echo "Setting up composite actions..."
copy_directory_recursive "$PROJECT_ROOT/.github/actions" "$PROJECT_ROOT/.github/actions" "$REPLACEMENTS"

# Create local testing directory if it doesn't exist
if [ ! -d "$PROJECT_ROOT/.github/local-testing" ]; then
  echo "Creating local testing directory..."
  mkdir -p "$PROJECT_ROOT/.github/local-testing"
  mkdir -p "$PROJECT_ROOT/.github/local-testing/events"
fi

# Create sample event files for local testing
cat > "$PROJECT_ROOT/.github/local-testing/events/push.json" << EOF
{
  "ref": "refs/heads/main",
  "before": "0000000000000000000000000000000000000000",
  "after": "1111111111111111111111111111111111111111",
  "repository": {
    "name": "$PROJECT_NAME",
    "full_name": "username/$PROJECT_NAME",
    "private": false
  },
  "pusher": {
    "name": "username",
    "email": "username@example.com"
  },
  "sender": {
    "login": "username"
  }
}
EOF

cat > "$PROJECT_ROOT/.github/local-testing/events/pull_request.json" << EOF
{
  "action": "opened",
  "number": 1,
  "pull_request": {
    "number": 1,
    "state": "open",
    "title": "Test PR",
    "body": "This is a test PR",
    "head": {
      "ref": "feature-branch",
      "sha": "2222222222222222222222222222222222222222"
    },
    "base": {
      "ref": "main",
      "sha": "1111111111111111111111111111111111111111"
    }
  },
  "repository": {
    "name": "$PROJECT_NAME",
    "full_name": "username/$PROJECT_NAME",
    "private": false
  },
  "sender": {
    "login": "username"
  }
}
EOF

# Create .actrc file if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.actrc" ]; then
  cat > "$PROJECT_ROOT/.actrc" << EOF
-P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
-P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04
-P ubuntu-20.04=ghcr.io/catthehacker/ubuntu:act-20.04
-P windows-latest=ghcr.io/catthehacker/ubuntu:act-latest
-P macos-latest=ghcr.io/catthehacker/ubuntu:act-latest
EOF
  echo "Created .actrc file for local testing"
fi

echo "Workflow setup completed successfully!"
echo "You can now run your workflows locally with:"
echo "  act -W .github/workflows/ci.yml"
echo "Or on GitHub by pushing to your repository"
