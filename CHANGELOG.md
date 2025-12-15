# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline with automated testing and Docker image building
- Docker image publishing to GitHub Container Registry (ghcr.io)
- Comprehensive CI/CD documentation in `.github/workflows/README.md`
- CI status badge in README
- Docker installation instructions in README
- Enhanced `.dockerignore` for optimized Docker builds
- Automated linting with flake8 in CI pipeline
- Test coverage reporting with pytest-cov
- This CHANGELOG file to track project changes

### Changed
- Updated Dockerfile to properly copy project files and dependencies
- Updated Dockerfile to include README.md in the container image
- Improved flake8 configuration for better code quality checks

### Fixed
- Removed unused `packages.txt` reference from Dockerfile

## [1.0.0] - 2024-01-15

### Added
- Initial release of Airflow Alerts Templates
- Modular alert system for email and Google Chat notifications
- Beautiful HTML email templates (success, retry, failure)
- Google Chat integration with rich card notifications and threading
- Configuration via Airflow Variables, environment variables, or function parameters
- Comprehensive test suite with pytest
- Example DAGs demonstrating usage
- Docker support with Astronomer Astro Runtime base image
- Docker Compose setup for local development
- R runtime and packages for data analysis
- Project documentation and usage guides

### Features
- `get_callbacks()` API for easy integration
- Individual callback functions for email and Google Chat
- Template customization support with Jinja2
- Production-ready error handling
- Thread ID support for Google Chat conversations

## [0.1.0] - Initial Development

### Added
- Basic project structure
- Alert utilities and templates
- Initial DAG examples

---

## Types of Changes

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes

[Unreleased]: https://github.com/abrahamkoloboe27/airflow-utils-templates/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/abrahamkoloboe27/airflow-utils-templates/releases/tag/v1.0.0
