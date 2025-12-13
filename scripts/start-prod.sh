#!/bin/bash
# Start production environment
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting production environment...${NC}"

# Safety check
if [ "$ENVIRONMENT" != "production" ]; then
    echo -e "${RED}⚠️ This script should only be run in production environment${NC}"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled${NC}"
        exit 0
    fi
fi

# Check required environment files
for env_file in environments/.env.production .env.app .env.db .env.cache .env.queue .env.security .env.logging; do
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}❌ Required environment file missing: $env_file${NC}"
        echo -e "${YELLOW}Please create it from the .example file and configure appropriately${NC}"
        exit 1
    fi
done

# Backup existing data
echo -e "${YELLOW}Creating backup...${NC}"
if docker-compose -f docker-compose.production.yml ps | grep -q db; then
    docker-compose -f docker-compose.production.yml exec -T db pg_dump -U postgres django_app_prod > backup_$(date +%Y%m%d_%H%M%S).sql
    echo -e "${GREEN}Backup created${NC}"
fi

# Start services
echo -e "${YELLOW}Starting production services...${NC}"
docker-compose -f docker-compose.production.yml up -d

# Wait for services
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 30

# Health check
echo -e "${YELLOW}Performing health check...${NC}"
if curl -f http://localhost/health/; then
    echo -e "${GREEN}✅ Production environment is healthy${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

echo -e "${GREEN}Production environment started successfully!${NC}"
echo ""
echo -e "${YELLOW}Monitoring commands:${NC}"
echo "  View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "  Check status: docker-compose -f docker-compose.production.yml ps"
echo "  Scale web workers: docker-compose -f docker-compose.production.yml up -d --scale web=3"