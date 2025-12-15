# CI/CD Pipeline

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### CI/CD Pipeline (`ci.yml`)

This workflow provides automated testing and Docker image building/publishing.

#### Triggers

- **Push** to `main`, `master`, or `develop` branches
- **Pull Requests** to `main`, `master`, or `develop` branches  
- **Tags** matching `v*.*.*` pattern (e.g., v1.0.0)
- **Manual trigger** via workflow_dispatch

#### Jobs

##### 1. Test Job
- Runs on every push and pull request
- Sets up Python 3.10 environment
- Installs project dependencies
- Runs pytest with coverage reporting
- Runs basic linting with flake8 (non-blocking)

##### 2. Build and Push Job
- Runs after successful tests
- Only executes on push events (not pull requests)
- Builds Docker image from `Dockerfile`
- Pushes image to GitHub Container Registry (ghcr.io)
- Tags images with:
  - Branch name (e.g., `main`, `develop`)
  - Commit SHA with branch prefix (e.g., `main-abc1234`)
  - Semantic version tags (for version tags like `v1.0.0`)
  - `latest` tag for default branch

#### Docker Image

The Docker image is based on Astronomer's Astro Runtime and includes:
- R runtime and packages for data analysis
- Python dependencies from `requirements.txt`
- The airflow-alerts package
- Custom templates

Images are published to: `ghcr.io/abrahamkoloboe27/airflow-utils-templates`

#### Permissions

The workflow requires:
- `contents: read` - to checkout the repository
- `packages: write` - to push images to GitHub Container Registry

#### Usage

To pull the latest image:

```bash
docker pull ghcr.io/abrahamkoloboe27/airflow-utils-templates:latest
```

To pull a specific version:

```bash
docker pull ghcr.io/abrahamkoloboe27/airflow-utils-templates:v1.0.0
```

To pull a branch-specific image:

```bash
docker pull ghcr.io/abrahamkoloboe27/airflow-utils-templates:main
```

## Local Development

To test the Docker build locally:

```bash
docker build -t airflow-utils-templates:local .
```

To run tests locally:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```
