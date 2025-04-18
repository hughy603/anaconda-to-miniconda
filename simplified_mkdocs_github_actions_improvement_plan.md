# Simplified MkDocs GitHub Actions Improvement Plan

This document outlines a simplified approach to improve the GitHub Actions validation process for publishing documentation to GitHub Pages using MkDocs. The focus is on practical, high-impact changes that meet industry Python standards for CLI tools without overcomplicating the project.

## Current System Overview

The current implementation includes:

- MkDocs with Material theme for documentation
- GitHub Actions workflow (`docs.yml`) for building and deploying documentation
- Python-based validation tools for GitHub Actions workflows
- Error handling and reporting system
- Multiple validation methods (CLI, VSCode, pre-commit)

## Key Areas for Improvement

After reviewing the current implementation, we've identified these key areas for improvement:

1. **CLI Structure**: Enhance the command-line interface for better usability
1. **Configuration Management**: Simplify configuration handling
1. **Documentation Workflow**: Improve the documentation build and deployment process
1. **Package Structure**: Optimize the package structure for maintainability
1. **Documentation**: Enhance documentation for users and contributors

## Simplified Recommendations

### 1. CLI Structure Improvements

**Current State**: The CLI uses a flat command structure with many options.

**Simplified Recommendation**:

- Implement a simple command group structure using Click
- Focus on the most common use cases
- Add clear help text with examples

```python
@click.group()
def cli():
    """GitHub Actions validation tools for documentation workflows."""
    pass


@cli.command()
@click.option("--workflow-file", help="Path to workflow file")
@click.option("--changed-only", is_flag=True, help="Only validate changed workflows")
def validate(workflow_file, changed_only):
    """Validate GitHub Actions workflows."""
    # Implementation
```

### 2. Configuration Management

**Current State**: Configuration is primarily handled through command-line arguments.

**Simplified Recommendation**:

- Add support for a simple configuration file (TOML format)
- Support basic environment variables for CI/CD environments
- Maintain a clear precedence: CLI args > env vars > config file > defaults

```python
def load_config():
    """Load configuration from file and environment."""
    config = {}

    # Load from config file if it exists
    config_file = Path(".github-actions-validator.toml")
    if config_file.exists():
        with open(config_file) as f:
            config.update(toml.load(f))

    # Environment variables override file config
    for key, value in os.environ.items():
        if key.startswith("GITHUB_ACTIONS_VALIDATOR_"):
            config_key = key[25:].lower()
            config[config_key] = value

    return config
```

### 3. Documentation Workflow Improvements

**Current State**: Basic MkDocs build and deploy to GitHub Pages.

**Simplified Recommendation**:

- Add a documentation preview command
- Implement PR documentation previews
- Add basic documentation quality checks

```yaml
# In docs.yml workflow
- name: Check documentation quality
  run: |
    uv pip install doc8 --system
    doc8 docs/

- name: Deploy PR preview
  if: github.event_name == 'pull_request'
  uses: peaceiris/actions-gh-pages@v4
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./site
    destination_dir: pr-${{ github.event.pull_request.number }}
```

### 4. Package Structure Optimization

**Current State**: The validation code is part of a larger package.

**Simplified Recommendation**:

- Keep the current structure but improve module organization
- Ensure clear separation of concerns
- Focus on making the code maintainable rather than extracting to a separate package

```
src/
├── github_actions_validator/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration handling
│   ├── validators/     # Validation logic
│   ├── runners/        # Execution runners
│   └── utils.py        # Utility functions
```

### 5. Documentation Enhancements

**Current State**: Basic documentation with some gaps.

**Simplified Recommendation**:

- Add a clear CLI reference page
- Include examples for common use cases
- Document configuration options
- Add troubleshooting section

## Implementation Approach

We recommend a phased approach to implement these improvements:

### Phase 1: CLI and Configuration (2 weeks)

- Implement the command group structure
- Add configuration file support
- Update help documentation

### Phase 2: Documentation Workflow (2 weeks)

- Add documentation preview command
- Implement PR documentation previews
- Add documentation quality checks

### Phase 3: Package Structure and Documentation (2 weeks)

- Refine module organization
- Enhance user documentation
- Add troubleshooting guide

## Benefits

This simplified approach will:

1. **Improve Usability**: Make the tools easier to use with better CLI structure
1. **Enhance Flexibility**: Support configuration files and environment variables
1. **Increase Documentation Quality**: Add quality checks and preview capabilities
1. **Maintain Simplicity**: Avoid overcomplicating the project structure
1. **Follow Industry Standards**: Align with Python best practices for CLI tools

## Next Steps

1. Review and approve this simplified plan
1. Prioritize the phases based on team needs
1. Implement Phase 1 and evaluate results before proceeding
1. Gather feedback from users throughout the process
