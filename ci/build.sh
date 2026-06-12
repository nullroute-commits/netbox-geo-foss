#!/bin/bash
# Build Docker images for all stages
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

IMAGE="netbox-geo"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/nullroute-commits/netbox-geo-foss}"
VERSION="${BUILD_VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo local)}"
PLATFORMS="${DOCKER_PLATFORMS:-linux/amd64,linux/arm64}"
PUSH="${PUSH:-false}"

echo -e "${GREEN}Building Docker images (version: $VERSION)...${NC}"

mkdir -p reports

build_stage() {
    local stage=$1 tag_suffix=$2
    local full_tag="$REGISTRY/$IMAGE:$VERSION$tag_suffix"
    echo -e "${YELLOW}→ Building $stage stage → $full_tag${NC}"

    if [ "${MULTI_ARCH:-false}" = "true" ]; then
        docker buildx build \
            --platform "$PLATFORMS" \
            --target "$stage" \
            --tag "$full_tag" \
            --tag "$REGISTRY/$IMAGE:latest$tag_suffix" \
            --cache-from "type=registry,ref=$REGISTRY/$IMAGE:ci-cache" \
            $( [ "$PUSH" = "true" ] && echo "--push" || echo "--load" ) \
            .
    else
        docker build \
            --target "$stage" \
            --tag "$IMAGE:$VERSION$tag_suffix" \
            --tag "$IMAGE:latest$tag_suffix" \
            .
    fi
    echo -e "${GREEN}  ✓ $stage built${NC}"
}

build_stage ci         "-ci"
build_stage production ""

# Smoke-test the production image
echo -e "${YELLOW}→ Smoke-testing production image${NC}"
docker run --rm "$IMAGE:latest" netbox-geo --help
echo -e "${GREEN}  ✓ Smoke test passed${NC}"

echo ""
echo -e "${GREEN}✓ Build complete${NC}"
