#!/bin/bash
# Start testing environment
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting testing environment...${NC}"

# Copy environment file if it doesn't exist
if [ ! -f environments/.env.testing ]; then
    echo -e "${YELLOW}Creating testing environment file...${NC}"
    cp environments/.env.testing.example environments/.env.testing
fi

# Run tests in Docker
echo -e "${YELLOW}Running tests in containerized environment...${NC}"
docker-compose -f docker-compose.testing.yml up --build --abort-on-container-exit

# Cleanup
echo -e "${YELLOW}Cleaning up test environment...${NC}"
docker-compose -f docker-compose.testing.yml down -v

echo -e "${GREEN}Testing completed!${NC}"