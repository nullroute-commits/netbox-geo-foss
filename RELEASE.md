# Release Process Guide

This document describes the release process for netbox-geo-foss.

## Prerequisites

Before creating a release, ensure:

1. All CI checks pass on the main branch
2. All tests pass locally and in CI
3. Code quality checks (black, flake8, isort, mypy) pass
4. Security scans (bandit, safety) show no critical issues
5. Documentation is up to date
6. CHANGELOG is updated with release notes

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Release Steps

### 1. Prepare the Release

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with release notes
3. Commit changes:
   ```bash
   git commit -m "Prepare release v1.0.0"
   git push origin main
   ```

### 2. Create and Push Tag

Create an annotated tag for the release:

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag to trigger release workflow
git push origin v1.0.0
```

### 3. Automated Release Process

Once the tag is pushed, GitHub Actions automatically:

1. **Creates GitHub Release**
   - Generates changelog from git commits
   - Creates release notes
   - Uploads release artifacts

2. **Builds Release Artifacts**
   - Builds Python wheel (`netbox_geo_foss-*.whl`)
   - Builds source distribution (`netbox_geo_foss-*.tar.gz`)
   - Uploads artifacts to GitHub Release

3. **Deploys Docker Image** (CD workflow)
   - Builds multi-arch Docker image
   - Pushes to GitHub Container Registry
   - Tags with version and `latest`

4. **Publishes to PyPI** (if configured)
   - Uploads wheel and source distribution
   - Makes package available via `pip install`

### 4. Verify Release

After the automated process completes, verify:

1. **GitHub Release**: Check https://github.com/nullroute-commits/netbox-geo-foss/releases
   - Release notes are accurate
   - Artifacts are attached

2. **Docker Image**: Verify image is available
   ```bash
   docker pull ghcr.io/nullroute-commits/netbox-geo-foss:v1.0.0
   docker pull ghcr.io/nullroute-commits/netbox-geo-foss:latest
   ```

3. **PyPI Package** (if published): Verify package is available
   ```bash
   pip install netbox-geo-foss==1.0.0
   ```

### 5. Post-Release Tasks

1. Update documentation website (if applicable)
2. Announce release on relevant channels
3. Create milestone for next release
4. Close any completed issues/PRs in the release milestone

## Rollback Process

If issues are found after release:

### Option 1: Patch Release

1. Fix the issue in main branch
2. Create patch release (e.g., v1.0.1)
3. Follow normal release process

### Option 2: Yanking Release (PyPI only)

If critical security issue or broken package:

```bash
# Yank release from PyPI (does not delete)
pip install twine
twine upload --skip-existing dist/*
```

Note: Cannot yank GitHub releases, only mark as draft/pre-release.

### Option 3: Delete Tag and Release

**Warning**: Only for immediately discovered critical issues.

```bash
# Delete remote tag
git push --delete origin v1.0.0

# Delete local tag
git tag -d v1.0.0

# Manually delete GitHub release via web interface
```

## Workflow Configuration

### Release Workflow (`.github/workflows/release.yml`)

Triggered by: Pushing a tag matching `v*`

Jobs:
- `create-release`: Creates GitHub release with generated changelog
- `build-artifacts`: Builds Python packages and uploads to release

### CD Workflow (`.github/workflows/cd.yml`)

Triggered by:
- Push to `main` branch
- Tags matching `v*`

Jobs:
- `deploy-docker`: Builds and pushes Docker image to GHCR
- `publish-pypi`: Publishes package to PyPI (tags only)

## Required Secrets

Configure these secrets in GitHub repository settings:

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- `PYPI_API_TOKEN`: PyPI API token for package publishing (optional)

## Testing Release Process

To test the release process without creating an actual release:

1. Create a test branch
2. Push a test tag (e.g., `test-v1.0.0`)
3. Monitor workflow execution
4. Delete test tag when done

## Troubleshooting

### Release Workflow Fails

1. Check workflow logs in GitHub Actions
2. Verify Python version compatibility (3.12+)
3. Ensure all dependencies are correctly specified
4. Verify build process works locally:
   ```bash
   python -m build
   ```

### Docker Build Fails

1. Test Docker build locally:
   ```bash
   docker build -t netbox-geo:test .
   ```
2. Check Dockerfile for syntax errors
3. Verify base image is available

### PyPI Upload Fails

1. Verify `PYPI_API_TOKEN` is configured correctly
2. Check package name is not already taken
3. Ensure version number is unique
4. Test upload to TestPyPI first:
   ```bash
   twine upload --repository testpypi dist/*
   ```

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
