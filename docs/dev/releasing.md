# Release Process

This document describes the process for releasing new versions of Conda-Forge Converter.

## Versioning

We follow [Semantic Versioning](https://semver.org/) for version numbers:

- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backwards-compatible)
- **PATCH** version: Bug fixes (backwards-compatible)

Version numbers are in the format `X.Y.Z` where:

- X is the major version
- Y is the minor version
- Z is the patch version

## Release Checklist

Before releasing a new version, complete the following checklist:

- [ ] All tests are passing in CI
- [ ] Code coverage meets or exceeds target (80%)
- [ ] Documentation is up-to-date
- [ ] CHANGELOG.md is updated with new features and fixes
- [ ] Version number is updated in relevant files
- [ ] All PRs for the milestone are merged or deferred

## Release Process

### 1. Prepare the Release

1. **Create a Release Branch**:

   ```bash
   git checkout develop
   git pull
   git checkout -b release/vX.Y.Z
   ```

1. **Update Version Number**:
   The version is automatically determined from git tags, but make sure any version references in documentation are updated.

1. **Update CHANGELOG.md**:

   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD

   ### Added
   - List of new features

   ### Changed
   - List of changes to existing functionality

   ### Fixed
   - List of bug fixes
   ```

1. **Build and Test Locally**:

   ```bash
   # Run tests
   pytest

   # Build package
   hatch build
   ```

1. **Commit Changes**:

   ```bash
   git add CHANGELOG.md
   git commit -m "Prepare release vX.Y.Z"
   ```

### 2. Review and Merge

1. **Create a Pull Request**:

   - Create a PR from `release/vX.Y.Z` to `main`
   - Request reviews from team members
   - Ensure CI passes

1. **Address Review Comments**:

   - Make any necessary changes
   - Push updates to the release branch

1. **Merge to Main**:

   ```bash
   # After approval
   git checkout main
   git merge --no-ff release/vX.Y.Z
   git push origin main
   ```

### 3. Tag and Release

1. **Create Git Tag**:

   ```bash
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   git push origin vX.Y.Z
   ```

1. **Create GitHub Release**:

   - Go to GitHub Releases
   - Create a new release from the tag
   - Use CHANGELOG.md content for the description
   - Attach built distribution files

1. **Publish to PyPI**:
   GitHub Actions will automatically build and publish to PyPI when a tag is pushed.

### 4. Post-Release

1. **Merge Back to Develop**:

   ```bash
   git checkout develop
   git merge --no-ff main
   git push origin develop
   ```

1. **Announce Release**:

   - Post announcement in relevant channels
   - Update documentation site

1. **Clean Up**:

   ```bash
   # Delete release branch
   git branch -d release/vX.Y.Z
   ```

## Automated Release with GitHub Actions

Our release process is automated with GitHub Actions:

1. When a tag is pushed, the CI workflow:
   - Runs tests
   - Builds the package
   - Publishes to PyPI
   - Creates a GitHub release

Example workflow trigger:

```yaml
on:
  push:
    tags:
      - 'v*'
```

## Emergency Hotfix Process

For critical bugs that need immediate fixes:

1. **Create Hotfix Branch**:

   ```bash
   git checkout main
   git pull
   git checkout -b hotfix/vX.Y.Z+1
   ```

1. **Make Fixes**:

   - Make minimal changes to fix the issue
   - Add tests

1. **Update Version and CHANGELOG**:

   ```bash
   # Update CHANGELOG.md with hotfix details
   ```

1. **Review and Merge**:

   - Create a PR to `main`
   - Get expedited review
   - Merge after approval

1. **Tag and Release**:

   - Follow standard tagging process
   - Clearly mark as hotfix in release notes

1. **Merge to Develop**:

   ```bash
   git checkout develop
   git merge --no-ff main
   git push origin develop
   ```

## Release Candidates

For major releases, we may publish release candidates:

1. **Create RC Branch**:

   ```bash
   git checkout develop
   git checkout -b release/vX.Y.Z-rc.1
   ```

1. **Tag RC**:

   ```bash
   git tag -a vX.Y.Z-rc.1 -m "Release candidate 1 for version X.Y.Z"
   git push origin vX.Y.Z-rc.1
   ```

1. **Test and Gather Feedback**:

   - Allow users to test the RC
   - Collect feedback and fix issues

1. **Proceed to Final Release**:

   - After sufficient testing, proceed with standard release process

## Release Schedule

We aim to follow this release schedule:

- **Patch releases**: As needed for bug fixes
- **Minor releases**: Every 1-2 months
- **Major releases**: Every 6-12 months

## Documentation Updates

For each release:

1. **Update Documentation**:

   - Ensure API documentation is current
   - Update examples if necessary
   - Update compatibility information

1. **Publish Documentation**:

   - Build and publish documentation site

## Conda-Forge Package Update

After a successful PyPI release:

1. **Update conda-forge Feedstock**:

   - Fork the conda-forge feedstock
   - Update meta.yaml with new version
   - Update SHA256 hash
   - Create PR to conda-forge

1. **Monitor Conda-Forge Build**:

   - Ensure package builds correctly on all platforms

## Post-Mortem

After each release:

1. **Review Process**:

   - Identify any issues in the release process
   - Update this document as needed

1. **Plan Next Release**:

   - Begin planning next milestone
