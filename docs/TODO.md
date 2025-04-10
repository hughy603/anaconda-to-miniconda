# Project TODO

## Documentation Tasks

### Completed

- [x] Simplified main README.md to be more concise
- [x] Enhanced docs/index.md as a comprehensive entry point
- [x] Simplified CONTRIBUTING.md to point to detailed documentation
- [x] Consolidated documentation guidelines in docs/dev/documentation.md
- [x] Simplified docs/user/cli-reference.md to be more direct and focused
- [x] Simplified docs/user/getting-started.md to essential information only
- [x] Fixed Ruff linting configuration in pyproject.toml
- [x] Simplified docs/index.md to be more concise and focused
- [x] Simplified docs/user/troubleshooting.md to focus on common issues
- [x] Simplified docs/user/workflows.md to show essential examples only
- [x] Review and update all internal documentation links
- [x] Create a changelog template
- [x] Ensure consistent formatting across all documentation
- [x] Add diagrams to architecture documentation
- [x] Created comprehensive CLI guide for system administrators
- [x] Created standardized documentation template
- [x] Created CLI documentation guide for developers
- [x] Updated GitHub issue templates for better clarity
- [x] Added system administrator specific issue template
- [x] Updated pull request templates
- [x] Created documentation improvement plan
- [x] Created quick reference cards for common CLI operations
- [x] Created a glossary of terms
- [x] Created a FAQ section based on common issues
- [x] Created printable cheat sheets for CLI commands
- [x] Updated mkdocs.yml to include all new documentation
- [x] Created a unified user issue template for all user issues

### Planned

- [ ] Add developer QoL features, like preventing memorization of long commands.
- [ ] Force Conventional Commit messages. Ensure incorrectly formatted messages are blocked.
- [ ] Apply standardized template to all existing documentation
- [ ] Create a sonar-project.properties that scans the uv dependency lock
- [ ] Add more examples for system administrators
- [ ] Organize TODO List
- [ ] Architect possible refactoring options for simplification

## Core Functionality Improvements

### High Priority

- [x] Enhanced error handling
- [x] Validation framework for post-conversion testing
- [x] Progress visualization for long-running operations
- [x] Cleanup options for original environments that will run after customers validate the converted environment
- [x] Add support for running as root and ensuring environments retain original ownership

### Medium Priority

- [ ] Advanced dependency analysis and conflict detection
- [ ] Custom conda configuration support
- [ ] Dependency pruning options
- [x] Caching layer for package metadata
- [ ] Container integration support
- [x] Batch package installation for improved performance
- [x] Integration with faster conda solvers (libmamba/mamba)

### Low Priority

- [ ] Notification system for long-running operations
- [ ] Improve backup process to optimize disk space. Don't create backup folders containing nothing.

## DevOps Improvements

### High Priority

- [x] Add test coverage reporting
- [x] Add security scanning
- [x] Add dependency caching
- [x] Add automated changelog generation
- [x] Add automated release process
- [x] Add automated documentation deployment

### Medium Priority

- [x] Add automated version bumping
- [x] Add automated release notes generation
- [x] Add automated changelog generation
- [x] Add automated documentation deployment
- [x] Add complexity metrics tracking
- [x] Consolidate and simplify GitHub Actions CI/CD pipelines

### Low Priority

- [x] Add contribution guidelines for documentation
- [x] Add automated documentation testing
- [x] Add automated documentation linting
