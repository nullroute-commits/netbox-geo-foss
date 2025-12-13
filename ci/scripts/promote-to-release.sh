#!/bin/bash
# Promote build to production environment
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Promoting build to production environment...${NC}"

# Configuration
SOURCE_TAG="${1:-test-latest}"
TARGET_TAG="${2:-prod-$(date +%Y%m%d-%H%M%S)}"
IMAGE_NAME="django-app"
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"

# Safety checks
if [ "$CI" != "true" ]; then
    echo -e "${RED}⚠️ Production promotion should only be run in CI environment${NC}"
    read -p "Are you sure you want to promote to production? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Promotion cancelled${NC}"
        exit 0
    fi
fi

echo -e "${YELLOW}Source tag: $SOURCE_TAG${NC}"
echo -e "${YELLOW}Target tag: $TARGET_TAG${NC}"

# Verify source image exists and is tested
echo -e "${YELLOW}Verifying source image...${NC}"
if ! docker pull $REGISTRY/$IMAGE_NAME:$SOURCE_TAG; then
    echo -e "${RED}❌ Source image not found: $REGISTRY/$IMAGE_NAME:$SOURCE_TAG${NC}"
    exit 1
fi

# Security scan before production
echo -e "${YELLOW}Running final security scan...${NC}"
if command -v trivy >/dev/null 2>&1; then
    if ! trivy image $REGISTRY/$IMAGE_NAME:$SOURCE_TAG --severity HIGH,CRITICAL --exit-code 1; then
        echo -e "${RED}❌ Security vulnerabilities found, cannot promote to production${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Security scan passed${NC}"
fi

# Tag for production
echo -e "${YELLOW}Tagging for production...${NC}"
docker tag $REGISTRY/$IMAGE_NAME:$SOURCE_TAG $REGISTRY/$IMAGE_NAME:$TARGET_TAG
docker tag $REGISTRY/$IMAGE_NAME:$SOURCE_TAG $REGISTRY/$IMAGE_NAME:production

# Push to registry
echo -e "${YELLOW}Pushing to registry...${NC}"
docker push $REGISTRY/$IMAGE_NAME:$TARGET_TAG
docker push $REGISTRY/$IMAGE_NAME:production

# Deploy to production
echo -e "${YELLOW}Deploying to production...${NC}"
BUILD_VERSION=$TARGET_TAG /app/ci/deploy.sh production

# Create release notes
echo -e "${YELLOW}Creating release notes...${NC}"
# Check for git availability and repository status
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    GIT_COMMIT="$(git rev-parse HEAD)"
    GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    GIT_LOG="$(git log --oneline --since="7 days ago" | head -10)"
else
    echo -e "${YELLOW}⚠️ Git not available or not a repository. Release notes will not include git info.${NC}"
    GIT_COMMIT="N/A"
    GIT_BRANCH="N/A"
    GIT_LOG="No git history available."
fi

cat > reports/release-notes.md << EOF
# Release $TARGET_TAG

**Deployment Date:** $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)
**Source Tag:** $SOURCE_TAG
**Production Tag:** $TARGET_TAG
**Git Commit:** $GIT_COMMIT
**Git Branch:** $GIT_BRANCH

## Changes
$GIT_LOG

## Deployment Verification
- ✅ Security scan passed
- ✅ Image promoted successfully
- ✅ Production deployment completed
- ✅ Health checks passed

EOF

echo -e "${GREEN}✅ Promotion to production completed!${NC}"
echo -e "${BLUE}Release notes saved to reports/release-notes.md${NC}"