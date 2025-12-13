#!/bin/bash
# CI/CD entrypoint script
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}  Django Multi-Architecture CI/CD Pipeline${NC}"
echo -e "${BLUE}===========================================${NC}"

# Display system information
echo -e "${YELLOW}System Information:${NC}"
echo "  Platform: $(uname -m)"
echo "  Python: $(python --version)"
echo "  Working Directory: $(pwd)"
echo "  User: $(whoami)"
echo ""

# Function to display help
show_help() {
    echo -e "${GREEN}Available CI/CD commands:${NC}"
    echo "  lint        - Run code quality checks"
    echo "  test        - Run all tests"
    echo "  test unit   - Run unit tests only"
    echo "  test integration - Run integration tests only"
    echo "  build       - Build Docker images"
    echo "  deploy      - Deploy to staging/production"
    echo "  security    - Run security scans"
    echo "  --help      - Show this help message"
    echo ""
    echo -e "${GREEN}Example usage:${NC}"
    echo "  docker-compose -f ci/docker-compose.ci.yml run ci-runner lint"
    echo "  docker-compose -f ci/docker-compose.ci.yml run ci-runner test"
    echo "  docker-compose -f ci/docker-compose.ci.yml run ci-runner build"
}

# Parse command line arguments
case "${1:-help}" in
    "lint")
        echo -e "${GREEN}Running code quality checks...${NC}"
        exec /app/ci/lint.sh
        ;;
    "test")
        if [ "$2" = "unit" ]; then
            echo -e "${GREEN}Running unit tests...${NC}"
            exec /app/ci/test.sh unit
        elif [ "$2" = "integration" ]; then
            echo -e "${GREEN}Running integration tests...${NC}"
            exec /app/ci/test.sh integration
        else
            echo -e "${GREEN}Running all tests...${NC}"
            exec /app/ci/test.sh
        fi
        ;;
    "build")
        echo -e "${GREEN}Building Docker images...${NC}"
        exec /app/ci/build.sh
        ;;
    "deploy")
        echo -e "${GREEN}Deploying application...${NC}"
        exec /app/ci/deploy.sh "$2"
        ;;
    "security")
        echo -e "${GREEN}Running security scans...${NC}"
        safety check -r requirements/base.txt
        bandit -r app/ -f json -o security-report.json || true
        ;;
    "--help"|"help"|*)
        show_help
        ;;
esac