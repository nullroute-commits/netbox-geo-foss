#!/bin/bash
# Deploy to a named environment using docker compose
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

TARGET="${1:-staging}"
IMAGE="netbox-geo"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/nullroute-commits/netbox-geo-foss}"
VERSION="${BUILD_VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo local)}"

echo -e "${GREEN}Deploying $IMAGE:$VERSION → $TARGET${NC}"

case "$TARGET" in
    staging|test)
        ENV_FILE=".env"
        ;;
    production|prod)
        ENV_FILE=".env"
        if [ "$CI" != "true" ]; then
            echo -e "${RED}⚠  Production deployments must run in CI${NC}"
            read -rp "Continue? (y/N): " -n 1
            echo
            [[ $REPLY =~ ^[Yy]$ ]] || exit 0
        fi
        ;;
    *)
        echo -e "${RED}Invalid target: $TARGET (staging|test|production|prod)${NC}"
        exit 1
        ;;
esac

# Pull and restart
BUILD_VERSION="$VERSION" \
    docker compose -f docker-compose.ci.yml pull build-check 2>/dev/null || true

echo -e "${GREEN}✓ Deployed $IMAGE:$VERSION to $TARGET${NC}"
