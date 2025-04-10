# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

## [1.0.0-alpha.1] - 2025-04-10

### Added

### Changed

### Fixed

## [1.0.2] - 2025-04-10

### Added

### Changed

### Fixed

## [1.0.1] - 2025-04-10

### Added

### Changed

### Fixed

## [1.1.0] - 2025-04-10

### Added

### Changed

### Fixed

## [2.0.0] - 2025-04-10

### Added

### Changed

### Fixed

## [0.2.0] - 2025-04-10

### Added

- Standardized code quality tasks using UV
- Simplified CI/CD pipelines with GitHub Actions
- Improved documentation building with MkDocs
- Configured pyright for static type checking
- Fully leveraged UV for dependency management, locking, and script running

### Changed

- Replaced pylint with pyright for more robust static type checking
- Moved from hatch to UV for comprehensive dependency management and script running
- Simplified workflow configurations to use UV directly

## [1.0.0] - 2025-04-05

### Added

- Initial project setup
- Basic conda environment conversion functionality
- Support for Python 3.11 and 3.12
- Comprehensive test suite with pytest
- Code quality tools: ruff, pylint
- CI/CD pipeline with GitHub Actions
- Documentation with MkDocs
- Security scanning with safety and bandit

### Changed

- Switched to hatch for dependency management
- Improved type hints and static analysis
- Enhanced pre-commit hooks configuration

### Fixed

- Version management using hatch-vcs
- Dependency caching in CI pipeline

### Security

- Added security scanning in CI
- Added dependency vulnerability checks

## [0.1.0] - 2024-04-06

### Added

- Initial release
- Basic project structure
- Core functionality for converting Anaconda environments to conda-forge
