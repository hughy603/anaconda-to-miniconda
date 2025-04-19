# Contributing to conda-forge-converter

Thank you for considering contributing to conda-forge-converter! This document provides a simplified overview of the contribution process.

## Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Install tools and dependencies
pipx install uv
pipx install pre-commit
uv pip install -e ".[dev,test]"

# Set up Git hooks
pre-commit install

# Configure Git (important for this project)
git config pull.rebase false

# Set up VSCode configuration (if using VSCode)
./scripts/setup_vscode.py
```

## Development Workflow

1. **Create a feature branch**: `git checkout -b feature/your-feature-name`
1. **Make your changes**: Implement your feature or bug fix
1. **Run pre-commit checks**: `pre-commit run --all-files`
1. **Run tests**: `pytest`
1. **Commit your changes**: Use conventional commit format (see below)
1. **Pull before pushing**: `git pull` (this will merge any remote changes)
1. **Push your changes**: `git push origin feature/your-feature-name`
1. **Submit a pull request**: Create a PR from your branch to the develop branch

## Branch Strategy

- **master**: Production branch for releases
- **develop**: Integration branch for features
- **feature/\***: Feature branches (branch from `develop`)
- **fix/\***: Bug fix branches (branch from `master` or `develop`)

## Conventional Commits

We use the [Conventional Commits](https://www.conventionalcommits.org/) standard for commit messages:

```
type(scope): description
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:

- `feat: add new feature`
- `fix(core): resolve issue with parser`

## Code Style and Quality

We use these tools for code quality:

- **Ruff**: Linting and formatting
- **Pyright**: Type checking
- **UV**: Dependency management
- **Pre-commit**: Automated checks

## Testing GitHub Actions Locally

```bash
# Validate workflow syntax
actionlint .github/workflows/your-workflow.yml

# Test workflow execution
.github/local-testing/local-test.sh .github/workflows/your-workflow.yml
```

For more details, see the [GitHub Actions Guide](github-actions-guide.md).

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We strive to maintain a welcoming and inclusive environment for everyone.

## Questions?

Feel free to open an issue if you have any questions about the contribution process.
