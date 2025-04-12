# Version Management

> **Note:** This guide has been simplified. For comprehensive information about version management, see the [README.md](README.md) and the [Conventional Commits section in CONTRIBUTING.md](CONTRIBUTING.md#conventional-commits).

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/) principles:

- MAJOR version for incompatible API changes
- MINOR version for backward-compatible functionality additions
- PATCH version for backward-compatible bug fixes

## Conventional Commits

We use [Conventional Commits](https://www.conventionalcommits.org/) to determine version bumps:

- `feat:` - Adds a new feature (MINOR version bump)
- `fix:` - Fixes a bug (PATCH version bump)
- `BREAKING CHANGE:` - Incompatible API change (MAJOR version bump)

## Quick Reference

### Manual Version Bumping

```bash
# Check what the next version would be
hatch run check-next-version

# Bump version (automatically determines level based on commits)
hatch run bump-version

# Prepare a release without pushing changes
hatch run prepare-release
```

### Release Process

1. Make changes and commit using conventional commit format
1. Merge to develop branch (CI/CD adds dev suffix)
1. Create PR from develop to master when ready for release
1. Merge PR to master and trigger release workflow manually

## Troubleshooting

If you encounter issues with version management:

1. Ensure you're using the conventional commit format
1. Check that your commits are on the correct branch
1. For manual fixes: `semantic-release version --new-version 1.2.3`
1. Debug version determination: `semantic-release version --print`
