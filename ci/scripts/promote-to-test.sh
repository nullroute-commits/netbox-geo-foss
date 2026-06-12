#!/bin/bash
# Promote a built image to the test environment tag
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

IMAGE="netbox-geo"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/nullroute-commits/netbox-geo-foss}"
SOURCE_TAG="${1:-latest}"
TARGET_TAG="${2:-test-$(date +%Y%m%d-%H%M%S)}"

echo -e "${GREEN}Promoting $IMAGE:$SOURCE_TAG → $TARGET_TAG${NC}"

docker pull "$REGISTRY/$IMAGE:$SOURCE_TAG"
docker tag  "$REGISTRY/$IMAGE:$SOURCE_TAG" "$REGISTRY/$IMAGE:$TARGET_TAG"
docker push "$REGISTRY/$IMAGE:$TARGET_TAG"

echo -e "${GREEN}✓ Promoted to test: $REGISTRY/$IMAGE:$TARGET_TAG${NC}"
