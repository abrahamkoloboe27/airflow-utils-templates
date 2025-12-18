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
- Optional logo/image support in email and Google Chat alert templates
- `logo_url` parameter for displaying custom branding in alerts
- Logo configuration via function parameter, environment variable (`AIRFLOW_ALERT_LOGO_URL`), or Airflow Variable (`alert_logo_url`)
- New `get_granular_callbacks()` function for fine-grained control over alert events
- `on_success`, `on_retry`, and `on_failure` boolean flags for granular alert control
- Custom SMTP connection support via `smtp_connection_id` parameter
- Custom Google Chat connection support via `gchat_connection_id` parameter
- Example DAG demonstrating logo usage (`example_dag_with_logo.py`)
- Example DAG demonstrating granular callbacks (`example_dag_granular_callbacks.py`)
- 10 new comprehensive tests for logo, granular callbacks, and custom connections
- **DAG-level alerts feature**: New `alert_level` parameter to choose between task-level or DAG-level alerts
- `dag_success_callback` and `dag_failure_callback` functions for email alerts with complete task summary
- `dag_success_callback` and `dag_failure_callback` functions for Google Chat alerts with task metrics
- New email templates: `dag_success.html` and `dag_failure.html` with task execution tables and statistics
- New Google Chat templates: `dag_success.json.j2` and `dag_failure.json.j2` with collapsible task details
- DAG-level alerts include comprehensive task metrics: success count, failure count, retry count, durations
- Failed task details in DAG-level failure alerts with error messages and execution times
- Example DAGs: `example_dag_level_alerts.py` and `example_dag_level_with_failures.py`
- Support for DAG-level alerts in both `get_callbacks()` and `get_granular_callbacks()` functions
- **DAG owner and tags display**: Automatic extraction and display of DAG owner(s) and tags in all alert templates
- Owner and tags information displayed in all email templates (success, retry, failure, dag_success, dag_failure)
- Owner and tags information displayed in all Google Chat templates (success, retry, failure, dag_success, dag_failure)
- Automatic extraction from DAG context without requiring code changes in existing DAGs

### Changed
- Updated Dockerfile to properly copy project files and dependencies
- Updated Dockerfile to include README.md in the container image
- Improved flake8 configuration for better code quality checks
- Enhanced `get_callbacks()` function to support logo_url, smtp_connection_id, and gchat_connection_id parameters
- Updated email templates (success, retry, failure) to display optional logo at the top
- Updated Google Chat templates to use optional logo in card headers
- Improved lambda closures to use default parameters avoiding late-binding issues

### Fixed
- Removed unused `packages.txt` reference from Dockerfile
- Lambda variable binding issues in callback functions to prevent late-binding problems

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
