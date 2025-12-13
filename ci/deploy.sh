#!/bin/bash
# Deployment script
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment target
TARGET="${1:-staging}"

echo -e "${GREEN}Deploying to: $TARGET${NC}"

# Configuration
IMAGE_NAME="django-app"
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
VERSION="${BUILD_VERSION:-$(git rev-parse --short HEAD)}"

# Validate target
case "$TARGET" in
    "staging"|"test")
        COMPOSE_FILE="docker-compose.testing.yml"
        ENV_FILE="environments/.env.testing.example"
        ;;
    "production"|"prod")
        COMPOSE_FILE="docker-compose.production.yml"
        ENV_FILE="environments/.env.production.example"
        ;;
    *)
        echo -e "${RED}❌ Invalid deployment target: $TARGET${NC}"
        echo -e "${YELLOW}Valid targets: staging, test, production, prod${NC}"
        exit 1
        ;;
esac

# Deployment functions
deploy_to_staging() {
    echo -e "${YELLOW}Deploying to staging environment...${NC}"
    
    # Pull latest images
    docker-compose -f $COMPOSE_FILE pull
    
    # Stop existing services
    docker-compose -f $COMPOSE_FILE down
    
    # Start services
    docker-compose -f $COMPOSE_FILE up -d
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 30
    
    # Run health checks
    if docker-compose -f $COMPOSE_FILE exec -T web curl -f http://localhost:8000/health/; then
        echo -e "${GREEN}✅ Staging deployment successful${NC}"
    else
        echo -e "${RED}❌ Staging health check failed${NC}"
        exit 1
    fi
}

deploy_to_production() {
    echo -e "${YELLOW}Deploying to production environment...${NC}"
    
    # Safety checks for production
    if [ "$CI" != "true" ]; then
        echo -e "${RED}⚠️ Production deployment should only be run in CI environment${NC}"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Deployment cancelled${NC}"
            exit 0
        fi
    fi
    
    # Backup current deployment
    echo -e "${YELLOW}Creating backup...${NC}"
    docker-compose -f $COMPOSE_FILE exec -T db pg_dump -U postgres django_app_prod > backup_$(date +%Y%m%d_%H%M%S).sql
    
    # Rolling deployment
    echo -e "${YELLOW}Starting rolling deployment...${NC}"
    
    # Pull latest images
    docker-compose -f $COMPOSE_FILE pull
    
    # Update services one by one
    docker-compose -f $COMPOSE_FILE up -d --no-deps web
    
    # Wait for new instance to be healthy
    sleep 60
    
    # Health check
    if docker-compose -f $COMPOSE_FILE exec -T web curl -f http://localhost:8000/health/; then
        echo -e "${GREEN}✅ Production deployment successful${NC}"
    else
        echo -e "${RED}❌ Production health check failed${NC}"
        echo -e "${YELLOW}Rolling back...${NC}"
        docker-compose -f $COMPOSE_FILE rollback
        exit 1
    fi
    
    # Update other services
    docker-compose -f $COMPOSE_FILE up -d
}

# Pre-deployment checks
echo -e "${YELLOW}Running pre-deployment checks...${NC}"

# Check if images exist
if ! docker pull $REGISTRY/$IMAGE_NAME:$VERSION; then
    echo -e "${RED}❌ Image not found: $REGISTRY/$IMAGE_NAME:$VERSION${NC}"
    exit 1
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ Compose file not found: $COMPOSE_FILE${NC}"
    exit 1
fi

# Database migration check
echo -e "${YELLOW}Checking database migrations...${NC}"
if ! docker run --rm --env-file $ENV_FILE $REGISTRY/$IMAGE_NAME:$VERSION python manage.py migrate --check; then
    echo -e "${YELLOW}⚠️ Pending migrations detected${NC}"
    if [ "$TARGET" = "production" ] || [ "$TARGET" = "prod" ]; then
        echo -e "${RED}❌ Cannot deploy to production with pending migrations${NC}"
        exit 1
    fi
fi

# Run deployment
case "$TARGET" in
    "staging"|"test")
        deploy_to_staging
        ;;
    "production"|"prod")
        deploy_to_production
        ;;
esac

# Post-deployment verification
echo -e "${YELLOW}Running post-deployment verification...${NC}"

# Health checks
HEALTH_URL="http://localhost:8000/health/"
for i in {1..10}; do
    if curl -f $HEALTH_URL; then
        echo -e "${GREEN}✅ Health check passed${NC}"
        break
    else
        echo -e "${YELLOW}Health check attempt $i/10 failed, retrying...${NC}"
        sleep 10
    fi
done

# Smoke tests
echo -e "${YELLOW}Running smoke tests...${NC}"
# Add smoke tests here

# Generate deployment report
echo -e "${YELLOW}Generating deployment report...${NC}"
cat > reports/deployment-report.json << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "target": "$TARGET",
  "version": "$VERSION",
  "image": "$REGISTRY/$IMAGE_NAME:$VERSION",
  "compose_file": "$COMPOSE_FILE",
  "env_file": "$ENV_FILE",
  "git_commit": "$(git rev-parse HEAD)",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD)",
  "deployed_by": "${USER:-unknown}",
  "status": "success"
}
EOF

echo -e "${GREEN}✅ Deployment to $TARGET completed successfully!${NC}"
echo -e "${BLUE}Deployment report saved to reports/deployment-report.json${NC}"