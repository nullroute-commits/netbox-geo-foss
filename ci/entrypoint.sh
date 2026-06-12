#!/bin/bash
# CI entrypoint – dispatches to individual ci/ scripts
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}=== NetBox Geo FOSS CI/CD Pipeline ===${NC}"
echo "  Python : $(python --version)"
echo "  Dir    : $(pwd)"
echo ""

show_help() {
    echo -e "${GREEN}Commands:${NC}"
    echo "  lint           Run black / flake8 / isort / mypy"
    echo "  test [unit|integration]  Run pytest suite"
    echo "  build          Build Docker images"
    echo "  deploy <env>   Deploy to environment (staging|production)"
    echo "  security       Run bandit + safety"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  docker compose -f docker-compose.ci.yml run --rm lint"
    echo "  docker compose -f docker-compose.ci.yml run --rm test"
}

case "${1:-help}" in
    lint)      exec /app/ci/lint.sh ;;
    test)      exec /app/ci/test.sh "${2:-all}" ;;
    build)     exec /app/ci/build.sh ;;
    deploy)    exec /app/ci/deploy.sh "${2:-staging}" ;;
    security)
        echo -e "${GREEN}Running security scans...${NC}"
        bandit -r src -f json -o reports/bandit-report.json || true
        safety check -r requirements/base.txt --json --output reports/safety-report.json || true
        ;;
    --help|help|*) show_help ;;
esac
