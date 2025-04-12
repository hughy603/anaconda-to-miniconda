#!/bin/bash
# Validate all GitHub Actions workflows by running them locally

# Default parameter values
CHANGED_ONLY=false
PARALLEL=false
MAX_PARALLEL=3
SECRETS_FILE=".github/local-secrets.json"
CACHE_PATH="./.act-cache"
CUSTOM_IMAGE=""
VERBOSE=false
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --changed-only)
      CHANGED_ONLY=true
      shift
      ;;
    --parallel)
      PARALLEL=true
      shift
      ;;
    --max-parallel)
      MAX_PARALLEL="$2"
      shift 2
      ;;
    --secrets-file)
      SECRETS_FILE="$2"
      shift 2
      ;;
    --cache-path)
      CACHE_PATH="$2"
      shift 2
      ;;
    --custom-image)
      CUSTOM_IMAGE="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --changed-only       Only validate workflows that have changed"
      echo "  --parallel           Run validations in parallel"
      echo "  --max-parallel N     Maximum number of parallel jobs (default: 3)"
      echo "  --secrets-file FILE  Path to secrets file (default: .github/local-secrets.json)"
      echo "  --cache-path PATH    Path to cache directory (default: ./.act-cache)"
      echo "  --full-matrix        Test all matrix combinations"
      echo "  --custom-image IMG   Use custom Docker image"
      echo "  --verbose            Enable verbose output"
      echo "  --dry-run            List workflows that would be validated without running them"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Function to format validation errors with helpful suggestions
format_validation_error() {
  local error_message="$1"
  local workflow_name="$2"

  # Check for common error patterns and provide suggestions
  if [[ "$error_message" == *"No such file or directory"* ]]; then
    echo "Error in $workflow_name: $error_message"
    echo "Suggestion: Check if all referenced files exist in the repository"
  elif [[ "$error_message" == *"Unknown action"* ]]; then
    echo "Error in $workflow_name: $error_message"
    echo "Suggestion: Make sure the action is publicly available or included in the repository"
  elif [[ "$error_message" == *"Invalid workflow file"* ]]; then
    echo "Error in $workflow_name: $error_message"
    echo "Suggestion: Validate the YAML syntax of your workflow file"
  elif [[ "$error_message" == *"not found"* ]]; then
    echo "Error in $workflow_name: $error_message"
    echo "Suggestion: Ensure the referenced resource exists and is accessible"
  elif [[ "$error_message" == *"permission denied"* ]]; then
    echo "Error in $workflow_name: $error_message"
    echo "Suggestion: Check file permissions or if you need elevated privileges"
  elif [[ "$error_message" == *"Could not find a version"* ]]; then
    echo "Error in $workflow_name: $error_message"
    echo "Suggestion: The specified package version may not exist or be available in the current environment"
  else
    echo "Error in $workflow_name: $error_message"
  fi
}

echo "Step 1: Validating workflow syntax with actionlint..."
pre-commit run actionlint --all-files

# Determine which workflows to validate
if [ "$CHANGED_ONLY" = true ]; then
  echo -e "\nIdentifying changed workflows..."
  changed_files=$(git diff --name-only HEAD | grep -E "^\.github/workflows/.*\.ya?ml$" || true)
  if [ -z "$changed_files" ]; then
    echo "No changed workflow files found."
    workflows=()
  else
    mapfile -t workflows <<< "$changed_files"
    echo "Found ${#workflows[@]} changed workflow files."
  fi
else
  echo -e "\nIdentifying all workflows..."
  mapfile -t workflows < <(find .github/workflows -name "*.yml" -o -name "*.yaml")
  echo "Found ${#workflows[@]} workflow files."
fi

if [ ${#workflows[@]} -eq 0 ]; then
  echo -e "\n✅ No workflows to validate."
  exit 0
fi

# If DRY_RUN is specified, just list the workflows that would be validated
if [ "$DRY_RUN" = true ]; then
  echo -e "\nDry run mode - would validate these workflows:"
  for workflow in "${workflows[@]}"; do
    echo "  - $(basename "$workflow")"
  done
  echo -e "\n✅ Dry run completed successfully."
  exit 0
fi

echo -e "\nStep 2: Running workflows in local containers with act..."

# Ensure cache directory exists
if [ ! -d "$CACHE_PATH" ]; then
  mkdir -p "$CACHE_PATH"
  echo "Created actions cache directory at $CACHE_PATH"
fi

# Check for secrets file
secrets_params=""
if [ -f "$SECRETS_FILE" ]; then
  echo "Using secrets from $SECRETS_FILE"
  secrets_params="--secret-file $SECRETS_FILE"
fi

# Add custom image if specified
platform_params=""
if [ -n "$CUSTOM_IMAGE" ]; then
  platform_params="-P $CUSTOM_IMAGE"
fi

# Add verbose flag if specified
verbose_params=""
if [ "$VERBOSE" = true ]; then
  verbose_params="--verbose"
fi

# Function to validate a single workflow
test_workflow() {
  local workflow="$1"
  local workflow_name
  workflow_name=$(basename "$workflow")

  echo -e "\n==== Testing workflow: $workflow_name ====\n"

  # Build command with all parameters
  cmd="./github-actions-local.sh -w $workflow --action-cache-path $CACHE_PATH $secrets_params $platform_params $verbose_params"

  # Execute the workflow validation
  if ! eval "$cmd"; then
    local exit_status=$?
    format_validation_error "Exit code $exit_status" "$workflow_name"
    return 1
  fi

  return 0
}

# Execute workflows based on parallel flag
success=true

if [ "$PARALLEL" = true ] && [ ${#workflows[@]} -gt 1 ]; then
  echo "Running validations in parallel (max $MAX_PARALLEL concurrent jobs)..."

  # Create a temporary directory for status files
  tmp_dir=$(mktemp -d)

  # Run workflows in parallel with GNU Parallel if available
  if command -v parallel &> /dev/null; then
    export -f test_workflow
    export -f format_validation_error
    export CACHE_PATH
    export secrets_params
    export platform_params
    export verbose_params

    parallel --jobs "$MAX_PARALLEL" --results "$tmp_dir" test_workflow ::: "${workflows[@]}"

    # Check results
    for result_file in "$tmp_dir"/*/stdout; do
      if [ ! -f "$result_file" ] || [ ! -s "$result_file" ] || grep -q "Error in" "$result_file"; then
        success=false
      fi
    done
  else
    echo "GNU Parallel not found, falling back to background processes"

    # Run workflows in background processes
    pids=()
    for workflow in "${workflows[@]}"; do
      test_workflow "$workflow" > "$tmp_dir/$(basename "$workflow").log" 2>&1 &
      pids+=($!)

      # Limit the number of parallel jobs
      if [ ${#pids[@]} -ge "$MAX_PARALLEL" ]; then
        wait "${pids[0]}"
        if [ $? -ne 0 ]; then
          success=false
        fi
        pids=("${pids[@]:1}")
      fi
    done

    # Wait for remaining processes
    for pid in "${pids[@]}"; do
      wait "$pid"
      if [ $? -ne 0 ]; then
        success=false
      fi
    done

    # Display logs
    for log_file in "$tmp_dir"/*.log; do
      cat "$log_file"
    done
  fi

  # Clean up
  rm -rf "$tmp_dir"
else
  for workflow in "${workflows[@]}"; do
    if ! test_workflow "$workflow"; then
      success=false
    fi
  done
fi

if [ "$success" = true ]; then
  echo -e "\n✅ All workflows validated successfully!"
  exit 0
else
  echo -e "\n❌ One or more workflows failed validation."
  exit 1
fi
