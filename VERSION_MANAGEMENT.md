# Version Management

This document describes the version management system used in this project.

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/) (SemVer) principles:

- MAJOR version for incompatible API changes
- MINOR version for backward-compatible functionality additions
- PATCH version for backward-compatible bug fixes
- Pre-release versions with alpha, beta, or rc suffixes

## Branch-Specific Versioning

The versioning behavior differs based on the branch:

### Master Branch

- Uses idempotent versioning (versions are permanent)
- Versions are tagged in Git
- Used for production releases
- Managed by Python-Semantic-Release

### Develop Branch

- Uses overwritable versioning with dev suffix
- No Git tags are created
- Used for development iterations
- Managed by Python-Semantic-Release

## Pre-release Versions

Pre-release versions are supported with the following format:

```
MAJOR.MINOR.PATCH-TYPE.NUMBER
```

Where:

- TYPE is one of: alpha, beta, rc, dev
- NUMBER is a sequential number starting from 1

Examples:

- 1.0.0-alpha.1
- 1.0.0-beta.2
- 1.0.0-rc.1
- 1.0.0-dev.5

## Version Bumping

### Manual Version Bumping

To manually bump the version, use the semantic-release command:

```bash
# Check what the next version would be without making changes
hatch run check-next-version

# Bump version (automatically determines level based on commits)
# This applies changes to files but doesn't commit or push
hatch run bump-version

# Prepare a release without pushing changes
hatch run prepare-release

# Force specific bump level
semantic-release version --patch
semantic-release version --minor
semantic-release version --major

# For a complete release (commit, tag, push, and publish)
semantic-release version
```

### Understanding Version Determination

Python-Semantic-Release analyzes your commit history to determine the next version:

1. It looks at all commits since the last release
1. It categorizes them based on the conventional commit type
1. It determines the appropriate version bump:
   - `fix:` commits trigger a PATCH bump (e.g., 1.0.0 → 1.0.1)
   - `feat:` commits trigger a MINOR bump (e.g., 1.0.0 → 1.1.0)
   - Commits with `BREAKING CHANGE:` in the body trigger a MAJOR bump (e.g., 1.0.0 → 2.0.0)

If no version-relevant commits are found, no version bump occurs.

### Automatic Version Bumping

Versions are automatically bumped in the CI/CD pipeline:

- Commits to develop: Bump to development version with dev suffix
- Releases from master: Create a release version based on conventional commits

### Release Process

The release process follows these steps:

1. **Prepare Changes**: Make your changes and commit them using conventional commit format
1. **Merge to Develop**: Changes are merged to the develop branch
   - The CI/CD pipeline automatically bumps the version with a dev suffix
   - This allows for testing pre-release versions
1. **Release Preparation**: When ready for release, create a PR from develop to master
1. **Release**: Merge the PR to master
   - Trigger the release workflow manually from GitHub Actions
   - The workflow will:
     - Determine the appropriate version bump based on commits
     - Update version files and changelog
     - Create a Git tag
     - Publish to PyPI
     - Create a GitHub release

## Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) to determine version bumps:

- `feat:` - Adds a new feature (MINOR version bump)
- `fix:` - Fixes a bug (PATCH version bump)
- `perf:` - Performance improvement (PATCH version bump)
- `BREAKING CHANGE:` - Incompatible API change (MAJOR version bump)
- Other types (no version bump, but included in changelog):
  - `docs:` - Documentation changes
  - `style:` - Code style changes (formatting, etc.)
  - `refactor:` - Code refactoring without functionality changes
  - `test:` - Adding or updating tests
  - `build:` - Changes to build system
  - `ci:` - Changes to CI configuration

### Commit Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Example:

```
feat(api): add new endpoint for user profiles

This adds a new REST API endpoint for retrieving user profiles.

BREAKING CHANGE: The old /profiles endpoint is removed in favor of the new /users/profiles endpoint.
```

### Best Practices for Commits

1. **Be Specific**: Write clear, concise descriptions
1. **Use Scopes**: Indicate which part of the codebase is affected
1. **One Change Per Commit**: Keep commits focused on a single change
1. **Reference Issues**: Use "Fixes #123" or "Relates to #456" in the footer
1. **Breaking Changes**: Always note breaking changes in the footer

## Changelog Management

The CHANGELOG.md file is automatically updated when bumping versions. It follows the [Keep a Changelog](https://keepachangelog.com/) format.

Python-Semantic-Release automatically:

1. Parses commit messages to determine the version bump
1. Updates the changelog with categorized changes
1. Maintains the [Unreleased] section for upcoming changes

## Version Synchronization

The version is stored in multiple places and kept in sync:

1. `pyproject.toml` - Uses dynamic versioning to get the version from \_version.py
1. `src/conda_forge_converter/_version.py` - Used for runtime version access
1. `CHANGELOG.md` - Documents changes for each version

The synchronization is handled automatically by Python-Semantic-Release.

## GitHub Workflow Integration

The GitHub workflows use Python-Semantic-Release to:

1. Validate release readiness
1. Determine the appropriate version bump based on commits
1. Update the version file and changelog
1. Create a GitHub release with release notes
1. Publish the package to PyPI

### Workflow Files

1. **version-bump.yml**: Automatically runs on pushes to the develop branch

   - Updates version with dev suffix
   - Does not create Git tags
   - Updates changelog

1. **release.yml**: Manually triggered for releases from the master branch

   - Can force a specific version bump type (patch, minor, major)
   - Creates Git tags
   - Updates changelog
   - Creates GitHub release
   - Publishes to PyPI

## Troubleshooting

If you encounter issues with version management:

1. Ensure you have Python-Semantic-Release installed:

   ```bash
   pip install python-semantic-release>=8.0.0
   ```

1. Check that the version files are properly configured:

   - `pyproject.toml` should have the semantic_release configuration
   - `src/conda_forge_converter/_version.py` should define `__version__`

1. For manual fixes, you can set the version directly:

   ```bash
   semantic-release version --new-version 1.2.3
   ```

1. To debug version determination:

   ```bash
   semantic-release version --print
   ```

1. If you see version 0.0.0 being reported:

   ```bash
   # Create an empty commit with the current version
   git commit --allow-empty -m "chore: initialize version 1.0.0-alpha.1"
   ```

1. If changes aren't being detected:

   - Make sure you're using the conventional commit format
   - Check that your commits are on the correct branch
   - Verify that the commit parser is configured correctly in pyproject.toml

1. For issues with the GitHub workflow:

   - Check the workflow logs for detailed error messages
   - Ensure the GH_TOKEN environment variable is properly set
   - Verify that the workflow has the necessary permissions
