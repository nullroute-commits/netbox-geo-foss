#!/bin/bash
# Test runner – unit, integration, or all
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

TEST_TYPE="${1:-all}"
echo -e "${GREEN}Running tests: $TEST_TYPE${NC}"

mkdir -p reports

# Pytest base args
BASE_ARGS=(
    --cov=netbox_geo
    --cov-report=html:reports/htmlcov
    --cov-report=xml:reports/coverage.xml
    --cov-report=term-missing
    --junitxml=reports/junit.xml
    -v
    --tb=short
)

case "$TEST_TYPE" in
    unit)
        pytest tests/unit/ "${BASE_ARGS[@]}"
        ;;
    integration)
        pytest tests/integration/ "${BASE_ARGS[@]}"
        ;;
    all|*)
        pytest tests/ "${BASE_ARGS[@]}"
        ;;
esac

EXIT=$?

echo ""
if [ $EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
fi
exit $EXIT
