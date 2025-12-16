# GitHub Actions Security Compliance Fix

**Date:** 2025-12-15  
**Issue:** Repository security policy requires all GitHub Actions to be pinned to full-length commit SHAs  
**Status:** ✅ RESOLVED  
**Commit:** d451614

## Problem

The repository has a security policy requiring all GitHub Actions to be pinned to full-length commit SHAs instead of tag references (e.g., @v4, @master). This prevents malicious actors from compromising workflows through tag manipulation.

**Error Message:**
```
The actions actions/checkout@v4 and github/codeql-action/init@v3 are not allowed in 
nullroute-commits/netbox-geo-foss because all actions must be pinned to a full-length commit SHA.
```

## Solution

Updated all 6 workflow files to pin every action to its full commit SHA while preserving the version tag in a comment for readability.

### Actions Updated (15 total)

| Action | Old Reference | New Reference | Version Tag |
|--------|---------------|---------------|-------------|
| actions/checkout | @v4 | @11bd71901bbe5b1630ceea73d27597364c9af683 | v4 |
| actions/setup-python | @v5 | @0b93645e9fea7318ecaed2b359559ac225c90a2b | v5 |
| actions/upload-artifact | @v4 | @b4b15b8c7c6ac21ea08fcf65892d2ee8f75cf882 | v4 |
| codecov/codecov-action | @v4 | @0f8570b1a125f4937846a11fcfa3bcd548bd8c97 | v4 |
| docker/build-push-action | @v5 | @ca052bb54ab0790a636c9b5f226502c73d547a25 | v5 |
| docker/login-action | @v3 | @9780b0c442fbb1117ed29e0efdff1e18412f7567 | v3 |
| docker/metadata-action | @v5 | @369eb591f429131d6889c46b94e711f089e6ca96 | v5 |
| docker/setup-buildx-action | @v3 | @c47758b77c9736f4b2ef4073d4d51994fabfe349 | v3 |
| github/codeql-action/init | @v3 | @6825d5659bf007b85a0866e2d0f434aacf50de94 | v3 |
| github/codeql-action/autobuild | @v3 | @6825d5659bf007b85a0866e2d0f434aacf50de94 | v3 |
| github/codeql-action/analyze | @v3 | @6825d5659bf007b85a0866e2d0f434aacf50de94 | v3 |
| github/codeql-action/upload-sarif | @v3 | @6825d5659bf007b85a0866e2d0f434aacf50de94 | v3 |
| aquasecurity/trivy-action | @master | @22438a435773de8c97dc0958cc0b823c45b064ac | master |
| hashicorp/setup-packer | @main | @76e3039aa951aa4e6efe7e6ee06bc9ceb072142d | main |
| softprops/action-gh-release | @v2 | @7b4da11513bf3f43f9999e90eabced41ab8bb048 | v2 |

### Files Modified

1. `.github/workflows/ci.yml` - 15 action references updated
2. `.github/workflows/cd.yml` - 7 action references updated
3. `.github/workflows/release.yml` - 5 action references updated
4. `.github/workflows/security-scan.yml` - 6 action references updated
5. `.github/workflows/codeql.yml` - 4 action references updated
6. `.github/workflows/ci-cd.yml` - 19 action references updated

**Total:** 56 action references updated across 6 files

## Implementation Details

### Format

Each action reference now follows this format:
```yaml
uses: action/name@<full-40-char-sha> # <version-tag>
```

**Example:**
```yaml
# Before
uses: actions/checkout@v4

# After
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4
```

The comment preserves the version tag for human readability and easier updates.

### SHA Retrieval Process

SHAs were retrieved using GitHub API:
```bash
curl -s https://api.github.com/repos/actions/checkout/git/ref/tags/v4.2.2 | \
  grep -o '"sha": "[^"]*"' | head -1 | cut -d'"' -f4
```

For branch references (master/main):
```bash
curl -s https://api.github.com/repos/aquasecurity/trivy-action/git/ref/heads/master | \
  grep -o '"sha": "[^"]*"' | head -1 | cut -d'"' -f4
```

## Validation

### YAML Syntax Validation

All workflow files validated as syntactically correct:
```
.github/workflows/ci.yml: ✓ Valid YAML
.github/workflows/cd.yml: ✓ Valid YAML
.github/workflows/release.yml: ✓ Valid YAML
.github/workflows/security-scan.yml: ✓ Valid YAML
.github/workflows/codeql.yml: ✓ Valid YAML
.github/workflows/ci-cd.yml: ✓ Valid YAML
```

### Verification

No unpinned actions remain:
```bash
$ grep -h "uses:" .github/workflows/*.yml | grep -E "@v[0-9]|@master|@main" | \
  grep -v "# v\|# master\|# main"
# (empty output - all actions pinned)
```

## Security Benefits

1. **Immutability:** Commit SHAs are immutable - they cannot be changed or moved
2. **Tag Protection:** Prevents attacks where tags are moved to malicious commits
3. **Audit Trail:** Clear record of exact action version used
4. **Compliance:** Meets repository security policy requirements

## Maintenance

When updating actions in the future:

1. Find the desired version tag
2. Retrieve the commit SHA for that tag
3. Update the SHA in the workflow file
4. Update the version comment to match

**Example update process:**
```bash
# Find latest v5 tag for actions/setup-python
curl -s https://api.github.com/repos/actions/setup-python/tags | \
  jq -r '.[0] | .name, .commit.sha'

# Update workflow file
# uses: actions/setup-python@<new-sha> # <new-version>
```

## References

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions)
- [Pinning Actions to Specific Versions](https://docs.github.com/en/actions/learn-github-actions/finding-and-customizing-actions#using-release-management-for-your-custom-actions)

---

**Result:** All GitHub Actions are now pinned to full-length commit SHAs, satisfying the repository security policy. ✅
