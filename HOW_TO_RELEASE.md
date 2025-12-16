# 🚀 How to Complete the Release

This guide provides step-by-step instructions to complete the v1.0.0 release after this PR is merged.

## Prerequisites

✅ This PR must be merged to the main branch first.

## Step 1: Merge the PR

1. Review and approve this PR: `copilot/debug-github-workflows-again`
2. Merge to `main` branch using GitHub's merge button
3. Wait for the merge to complete

## Step 2: Update Your Local Repository

```bash
# Switch to main branch
git checkout main

# Pull the latest changes
git pull origin main

# Verify you're on the latest commit
git log -1
```

## Step 3: Create and Push the Release Tag

```bash
# Create an annotated tag for version 1.0.0
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial FOSS release"

# Verify the tag was created
git tag -l -n1

# Push the tag to GitHub (this triggers the release workflow)
git push origin v1.0.0
```

## Step 4: Monitor Workflow Execution

Once you push the tag, GitHub Actions will automatically start three workflows:

### 1. Release Workflow
- **URL:** https://github.com/nullroute-commits/netbox-geo-foss/actions/workflows/release.yml
- **Duration:** ~2-5 minutes
- **Creates:**
  - GitHub Release with automated changelog
  - Python wheel package (`.whl`)
  - Source distribution (`.tar.gz`)

### 2. CD Workflow  
- **URL:** https://github.com/nullroute-commits/netbox-geo-foss/actions/workflows/cd.yml
- **Duration:** ~5-10 minutes
- **Creates:**
  - Docker image pushed to GHCR
  - Tags: `v1.0.0`, `latest`, `<sha>`
  - (Optional) PyPI publication if PYPI_API_TOKEN is configured

### 3. CI Workflow
- **URL:** https://github.com/nullroute-commits/netbox-geo-foss/actions/workflows/ci.yml
- **Duration:** ~3-7 minutes
- **Validates:**
  - Code quality checks pass
  - All tests pass
  - Build succeeds

## Step 5: Verify the Release

### Check GitHub Release

1. Go to: https://github.com/nullroute-commits/netbox-geo-foss/releases
2. Verify release v1.0.0 is created
3. Check that artifacts are attached:
   - `netbox_geo_foss-1.0.0-py3-none-any.whl`
   - `netbox_geo_foss-1.0.0.tar.gz`
4. Review the generated changelog

### Verify Docker Image

```bash
# Pull the image with version tag
docker pull ghcr.io/nullroute-commits/netbox-geo-foss:v1.0.0

# Pull the latest tag
docker pull ghcr.io/nullroute-commits/netbox-geo-foss:latest

# Verify the images
docker images | grep netbox-geo-foss

# Test the image (optional)
docker run --rm ghcr.io/nullroute-commits/netbox-geo-foss:v1.0.0 netbox-geo --version
```

### Verify PyPI Package (if published)

```bash
# Check if package is available on PyPI
pip search netbox-geo-foss

# Install the package
pip install netbox-geo-foss==1.0.0

# Verify installation
netbox-geo --version
```

## Troubleshooting

### Issue: Tag push fails with authentication error

**Cause:** Git credentials not configured correctly

**Solution:**
```bash
# Ensure you're authenticated with GitHub
gh auth status

# If not authenticated
gh auth login
```

### Issue: Release workflow fails

**Cause:** Various potential issues

**Solution:**
1. Check the workflow logs in GitHub Actions
2. Look for the specific error message
3. Common fixes:
   - Ensure `pyproject.toml` version matches tag (v1.0.0)
   - Verify all required files exist
   - Check Python version compatibility

### Issue: Docker build fails

**Cause:** Build errors or missing dependencies

**Solution:**
1. Test Docker build locally:
   ```bash
   docker build -t test .
   ```
2. Check the Dockerfile for errors
3. Verify all dependencies are in requirements files

### Issue: PyPI upload fails

**Cause:** Missing or invalid PYPI_API_TOKEN secret

**Solution:**
1. This is optional - workflow will continue without PyPI publishing
2. To enable PyPI publishing:
   - Create PyPI API token at https://pypi.org/manage/account/token/
   - Add as GitHub secret: `PYPI_API_TOKEN`
   - Re-run the workflow

## What Happens After Release?

1. **GitHub Release** is created with v1.0.0
2. **Docker images** are available at:
   - `ghcr.io/nullroute-commits/netbox-geo-foss:v1.0.0`
   - `ghcr.io/nullroute-commits/netbox-geo-foss:latest`
3. **Python packages** are attached to the GitHub release
4. **(Optional)** Package is published to PyPI if configured
5. **Release notes** are automatically generated from commits

## Post-Release Activities

After a successful release:

1. **Announce the release:**
   - Update project README with release badge
   - Post on relevant forums/channels
   - Update documentation site

2. **Plan next release:**
   - Create milestone for v1.1.0
   - Start tracking features/bugs for next release
   - Update CHANGELOG.md with Unreleased section

3. **Monitor for issues:**
   - Watch for bug reports
   - Monitor GitHub Issues
   - Respond to user feedback

## Rolling Back (if needed)

If critical issues are found immediately after release:

### Quick Fix (Recommended)
Create a patch release (v1.0.1) with the fix:
```bash
# Fix the issue in main branch
git commit -m "Fix critical issue"
git push origin main

# Create patch release
git tag -a v1.0.1 -m "Patch release - Fix critical issue"
git push origin v1.0.1
```

### Delete Release (Nuclear Option)
Only if absolutely necessary:
```bash
# Delete remote tag
git push --delete origin v1.0.0

# Delete local tag  
git tag -d v1.0.0

# Manually delete GitHub release via web interface
# Go to: Releases → v1.0.0 → Delete
```

## Need Help?

- **Workflow Logs:** https://github.com/nullroute-commits/netbox-geo-foss/actions
- **Release Process:** See `RELEASE.md`
- **Changelog:** See `CHANGELOG.md`
- **Issues:** https://github.com/nullroute-commits/netbox-geo-foss/issues

---

**Ready to release? Let's go! 🚀**

After merging this PR, just follow Steps 2-5 above to complete your first production release.
