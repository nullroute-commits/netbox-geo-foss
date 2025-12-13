#!/bin/bash
# Build script for Docker images
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Docker images...${NC}"

# Configuration
IMAGE_NAME="django-app"
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
VERSION="${BUILD_VERSION:-$(git rev-parse --short HEAD)}"
PLATFORMS="${DOCKER_PLATFORMS:-linux/amd64,linux/arm64}"

# Build arguments
BUILD_ARGS=(
    "--build-arg" "PYTHON_VERSION=3.12.5"
    "--build-arg" "BUILDKIT_INLINE_CACHE=1"
)

# Function to build multi-architecture image
build_multiarch_image() {
    local target=$1
    local tag_suffix=$2
    
    echo -e "${YELLOW}Building multi-architecture image: $target${NC}"
    
    docker buildx build \
        --platform $PLATFORMS \
        --target $target \
        --tag $REGISTRY/$IMAGE_NAME:$VERSION$tag_suffix \
        --tag $REGISTRY/$IMAGE_NAME:latest$tag_suffix \
        "${BUILD_ARGS[@]}" \
        --cache-from type=registry,ref=$REGISTRY/$IMAGE_NAME:buildcache \
        --cache-to type=registry,ref=$REGISTRY/$IMAGE_NAME:buildcache,mode=max \
        --push \
        .
}

# Function to build local image for testing
build_local_image() {
    local target=$1
    local tag_suffix=$2
    
    echo -e "${YELLOW}Building local image: $target${NC}"
    
    docker build \
        --target $target \
        --tag $IMAGE_NAME:$VERSION$tag_suffix \
        --tag $IMAGE_NAME:latest$tag_suffix \
        "${BUILD_ARGS[@]}" \
        .
}

# Initialize Docker Buildx
echo -e "${YELLOW}Initializing Docker Buildx...${NC}"
docker buildx create --name multiarch --driver docker-container --use 2>/dev/null || \
docker buildx use multiarch

# Verify platforms
echo -e "${YELLOW}Available platforms:${NC}"
docker buildx inspect --bootstrap

# Build development image
echo -e "${BLUE}Building development image...${NC}"
if [ "${MULTI_ARCH:-false}" = "true" ]; then
    build_multiarch_image "development" "-dev"
else
    build_local_image "development" "-dev"
fi

# Build testing image
echo -e "${BLUE}Building testing image...${NC}"
if [ "${MULTI_ARCH:-false}" = "true" ]; then
    build_multiarch_image "testing" "-test"
else
    build_local_image "testing" "-test"
fi

# Build production image
echo -e "${BLUE}Building production image...${NC}"
if [ "${MULTI_ARCH:-false}" = "true" ]; then
    build_multiarch_image "production" ""
else
    build_local_image "production" ""
fi

# Test images
echo -e "${YELLOW}Testing built images...${NC}"

# Test development image
echo -e "${YELLOW}Testing development image...${NC}"
if docker run --rm $IMAGE_NAME:latest-dev python --version; then
    echo -e "${GREEN}✅ Development image test passed${NC}"
else
    echo -e "${RED}❌ Development image test failed${NC}"
    exit 1
fi

# Test production image
echo -e "${YELLOW}Testing production image...${NC}"
if docker run --rm $IMAGE_NAME:latest python --version; then
    echo -e "${GREEN}✅ Production image test passed${NC}"
else
    echo -e "${RED}❌ Production image test failed${NC}"
    exit 1
fi

# Image size analysis
echo -e "${YELLOW}Analyzing image sizes...${NC}"
docker images | grep $IMAGE_NAME

# Security scan (if trivy is available)
if command -v trivy >/dev/null 2>&1; then
    echo -e "${YELLOW}Running security scan...${NC}"
    trivy image $IMAGE_NAME:latest --format json --output reports/security-scan.json || true
    echo -e "${GREEN}✅ Security scan completed${NC}"
else
    echo -e "${YELLOW}⚠️ Trivy not installed, skipping security scan${NC}"
fi

# Generate build report
echo -e "${YELLOW}Generating build report...${NC}"
cat > reports/build-report.json << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "$VERSION",
  "platforms": "$PLATFORMS",
  "registry": "$REGISTRY",
  "images": {
    "development": "$REGISTRY/$IMAGE_NAME:$VERSION-dev",
    "testing": "$REGISTRY/$IMAGE_NAME:$VERSION-test",
    "production": "$REGISTRY/$IMAGE_NAME:$VERSION"
  },
  "build_args": $(printf '%s\n' "${BUILD_ARGS[@]}" | jq -R . | jq -s .),
  "git_commit": "$(git rev-parse HEAD)",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD)"
}
EOF

echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo -e "${BLUE}Build report saved to reports/build-report.json${NC}"