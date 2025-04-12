# Contributing to conda-forge-converter

Thank you for considering contributing to conda-forge-converter! This document provides a brief overview of the contribution process.

For comprehensive contribution guidelines, please refer to the following documentation:

- [Developer Workflow Guide](docs/dev/workflow.md) - Complete development process
- [Conventional Commits Guide](docs/dev/conventional-commits.md) - How to format commit messages
- [Build Tools Guide](docs/dev/build-tools.md) - Information about our build and version management tools
- [Pull Request Process](docs/dev/pr-process.md) - How to submit and review PRs
- [Quick Reference](docs/dev/quick-reference.md) - Cheat sheet for common tasks

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter

# Install UV (recommended to use pipx for global installation)
pip install uv

# Install shellcheck (required for pre-commit hooks)
# On Windows: scoop install shellcheck
# On macOS: brew install shellcheck
# On Ubuntu/Debian: apt-get install shellcheck
# On Fedora/RHEL: dnf install ShellCheck

# Set up development environment
uv venv
uv pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push  # Ensures all files are checked before pushing

# Configure Git to use merge strategy for pulls (important for this project)
git config pull.rebase false

# Set up VSCode configuration (if using VSCode)
./scripts/setup_vscode.py
```

### VSCode Setup

If you're using VSCode, we provide pre-configured settings to help you get started quickly:

1. Run the setup script to configure VSCode:

   ```bash
   ./scripts/setup_vscode.py
   ```

1. This will create a `.vscode` directory with:

   - Debug configurations for conda/mamba integration
   - Recommended settings for Python development
   - Tasks for common development operations
   - Recommended extensions

1. For detailed information on debugging with VSCode, see the [VSCode Debugging Guide](docs/dev/vscode-debugging.md).

## Git Configuration

To prevent issues with divergent branches when working with this project, it's important to configure Git to use the merge strategy for pulls:

```bash
git config pull.rebase false
```

You can also set this globally for all repositories:

```bash
git config --global pull.rebase false
```

This ensures that when you pull changes that include automatic version bump commits, Git will automatically create a merge commit instead of failing with divergent branch errors.

## Development Workflow Summary

1. **Create a feature branch**: `git checkout -b feature/your-feature-name`

1. **Make your changes**: Implement your feature or bug fix

1. **Run pre-commit checks**: `pre-commit run --all-files`

   - Note: A pre-push hook has been added that automatically runs this check before pushing, helping prevent CI failures due to formatting or linting issues
   - The pre-push hook will block pushes if any linting or formatting issues are found, ensuring code quality standards are maintained
   - Many hooks are configured to automatically fix issues when possible (like ruff with --fix flag)

- The pre-push hook will block pushes if any linting or formatting issues are found, ensuring code quality standards are maintained
  - Note: A pre-push hook has been added that automatically runs this check before pushing, helping prevent CI failures due to formatting or linting issues

1. **Run tests**: `pytest`

1. **Test GitHub Actions workflows locally** (if applicable):

   ```bash
   # Validate workflow syntax
   actionlint .github/workflows/your-workflow.yml

   # Test workflow execution
   .github/local-testing/test-workflow.sh .github/workflows/your-workflow.yml
   ```

   For detailed information on testing GitHub Actions workflows locally, see the [GitHub Actions Guide](github-actions-guide.md).

1. **Commit your changes**: Use conventional commit format (see below)

1. **Pull before pushing**: `git pull` (this will merge any remote changes)

1. **Push your changes**: `git push origin feature/your-feature-name`

1. **Submit a pull request**: Create a PR from your branch to the develop branch

## Branch Strategy

This project uses the following branch strategy:

- **master**: The production branch. All releases are made from this branch.
- **develop**: The integration branch for features. All feature branches should be created from and merged back to this branch.
- **feature/\***: Feature branches for new development. Always branch from `develop`.
- **fix/\***: Bug fix branches. Can branch from either `master` (for hotfixes) or `develop` (for regular fixes).

The workflow is:

1. Create feature branches from `develop`
1. Submit PRs to merge feature branches into `develop`
1. Periodically, `develop` is merged into `master` for releases

## Conventional Commits

We use the [Conventional Commits](https://www.conventionalcommits.org/) standard for commit messages. This is enforced by pre-commit hooks.

Basic format:

```
type(scope): description
```

Common types:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `refactor`: Code restructuring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

For detailed examples and guidelines, see the [Conventional Commits Guide](docs/dev/conventional-commits.md).

## Code Style

We use Ruff for linting and formatting, and Pyright for type checking. These tools are configured in `pyproject.toml` and run automatically via pre-commit hooks.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We strive to maintain a welcoming and inclusive environment for everyone.

## Questions?

Feel free to open an issue if you have any questions or need clarification on any aspect of the contribution process.
