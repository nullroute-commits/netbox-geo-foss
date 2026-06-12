#!/bin/bash
# Promote a tested image to the production/release tag
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

IMAGE="netbox-geo"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/nullroute-commits/netbox-geo-foss}"
SOURCE_TAG="${1:-test-latest}"
TARGET_TAG="${2:-release-$(date +%Y%m%d-%H%M%S)}"

if [ "$CI" != "true" ]; then
    echo -e "${RED}⚠  Production promotion should run in CI only${NC}"
    read -rp "Continue anyway? (y/N): " -n 1
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || exit 0
fi

echo -e "${GREEN}Promoting $IMAGE:$SOURCE_TAG → production ($TARGET_TAG)${NC}"

docker pull "$REGISTRY/$IMAGE:$SOURCE_TAG"

# Optional: security gate via Trivy
if command -v trivy >/dev/null 2>&1; then
    echo -e "${YELLOW}→ Running security gate (Trivy)${NC}"
    trivy image "$REGISTRY/$IMAGE:$SOURCE_TAG" --severity HIGH,CRITICAL --exit-code 1
fi

docker tag  "$REGISTRY/$IMAGE:$SOURCE_TAG" "$REGISTRY/$IMAGE:$TARGET_TAG"
docker tag  "$REGISTRY/$IMAGE:$SOURCE_TAG" "$REGISTRY/$IMAGE:production"
docker push "$REGISTRY/$IMAGE:$TARGET_TAG"
docker push "$REGISTRY/$IMAGE:production"

echo -e "${GREEN}✓ Released: $REGISTRY/$IMAGE:production ($TARGET_TAG)${NC}"
