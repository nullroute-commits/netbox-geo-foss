#!/bin/bash
# Promote build to test environment
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Promoting build to test environment...${NC}"

# Configuration
SOURCE_TAG="${1:-latest}"
TARGET_TAG="${2:-test-$(date +%Y%m%d-%H%M%S)}"
IMAGE_NAME="django-app"
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"

echo -e "${YELLOW}Source tag: $SOURCE_TAG${NC}"
echo -e "${YELLOW}Target tag: $TARGET_TAG${NC}"

# Pull source image
echo -e "${YELLOW}Pulling source image...${NC}"
docker pull $REGISTRY/$IMAGE_NAME:$SOURCE_TAG

# Tag for test environment
echo -e "${YELLOW}Tagging for test environment...${NC}"
docker tag $REGISTRY/$IMAGE_NAME:$SOURCE_TAG $REGISTRY/$IMAGE_NAME:$TARGET_TAG

# Push to registry
echo -e "${YELLOW}Pushing to registry...${NC}"
docker push $REGISTRY/$IMAGE_NAME:$TARGET_TAG

# Deploy to test environment
echo -e "${YELLOW}Deploying to test environment...${NC}"
BUILD_VERSION=$TARGET_TAG /app/ci/deploy.sh test

echo -e "${GREEN}✅ Promotion to test environment completed!${NC}"