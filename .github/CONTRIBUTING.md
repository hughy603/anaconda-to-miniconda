# Contributing to Anaconda to Miniconda

We love your input! We want to make contributing as easy and transparent as possible.

## Development Process

1. Fork the repo
1. Create a feature branch (`git checkout -b feature/amazing-feature`)
1. Make your changes
1. Run tests (`uvx pytest`)
1. Run linting (`uvx pre-commit run --all-files`)
1. Commit your changes using the Conventional Commit format (`git commit -m 'feat: add amazing feature'`)
1. Push to the branch (`git push origin feature/amazing-feature`)
1. Open a Pull Request using the appropriate PR template

## Code Style

- We use `black` for code formatting
- We use `ruff` for linting
- We use `mypy` for type checking
- All Python code must be type-annotated
- Follow PEP 8 guidelines

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting PR
- Aim for 80% code coverage
- Use `pytest` for testing

## Documentation

- Update documentation for any new features
- Follow Google style for docstrings
- Keep README.md up to date
- Update CHANGELOG.md for significant changes

## Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) standard for commit messages:

```
<type>(<optional scope>): <description>

<optional body>

<optional footer(s)>
```

Common types include:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Changes that don't affect code functionality
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or correcting tests
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration
- `chore`: Other changes that don't modify src or test files

Examples:

- `feat(cli): add new validation command`
- `fix(core): resolve environment parsing issue`
- `docs: update installation instructions`

## Pull Request Process

1. Choose the appropriate PR template based on your change type:
   - Feature additions: Use the "Feature Addition" template
   - Bug fixes: Use the "Bug Fix" template
   - Documentation changes: Use the "Documentation Update" template
   - Code refactoring: Use the "Code Refactoring" template
   - For other changes: Use the default template
1. Format your PR title following the Conventional Commit format
1. Update the README.md with details of changes if needed
1. Update the CHANGELOG.md with details of changes
1. The PR will be merged once you have a maintainer's approval
1. Ensure the PR description clearly describes the problem and solution

## Questions?

Feel free to open an issue for any questions about contributing.
