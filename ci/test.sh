#!/bin/bash
# Test execution script
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test type (default: all)
TEST_TYPE="${1:-all}"

echo -e "${GREEN}Running tests: $TEST_TYPE${NC}"

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services...${NC}"
while ! nc -z ${POSTGRES_HOST:-test-db} ${POSTGRES_PORT:-5432}; do sleep 1; done
while ! nc -z ${MEMCACHED_SERVERS%%:*:-test-memcached} ${MEMCACHED_SERVERS##*::-11211}; do sleep 1; done
while ! nc -z ${RABBITMQ_HOST:-test-rabbitmq} ${RABBITMQ_PORT:-5672}; do sleep 1; done
echo -e "${GREEN}Services are ready!${NC}"

# Create reports directory
mkdir -p reports/coverage

# Set environment variables for testing
export DJANGO_SETTINGS_MODULE=config.settings.testing
export DATABASE_URL="postgresql://postgres:ci-password@${POSTGRES_HOST:-test-db}:${POSTGRES_PORT:-5432}/django_app_ci"

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate --noinput

# Function to run unit tests
run_unit_tests() {
    echo -e "${YELLOW}Running unit tests...${NC}"
    pytest tests/unit/ \
        -v \
        --tb=short \
        --cov=app \
        --cov-report=html:reports/coverage/unit-html \
        --cov-report=xml:reports/coverage/unit-coverage.xml \
        --cov-report=term \
        --junitxml=reports/unit-test-results.xml \
        --maxfail=10 \
        -x
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${YELLOW}Running integration tests...${NC}"
    pytest tests/integration/ \
        -v \
        --tb=short \
        --cov=app \
        --cov-report=html:reports/coverage/integration-html \
        --cov-report=xml:reports/coverage/integration-coverage.xml \
        --cov-report=term \
        --junitxml=reports/integration-test-results.xml \
        --maxfail=5 \
        -x
}

# Function to run all tests
run_all_tests() {
    echo -e "${YELLOW}Running all tests...${NC}"
    pytest tests/ \
        -v \
        --tb=short \
        --cov=app \
        --cov-report=html:reports/coverage/all-html \
        --cov-report=xml:reports/coverage/all-coverage.xml \
        --cov-report=term \
        --junitxml=reports/all-test-results.xml \
        --maxfail=10 \
        --durations=10 \
        -n auto
}

# Exit code tracking
EXIT_CODE=0

# Run tests based on type
case "$TEST_TYPE" in
    "unit")
        if ! run_unit_tests; then
            EXIT_CODE=1
        fi
        ;;
    "integration")
        if ! run_integration_tests; then
            EXIT_CODE=1
        fi
        ;;
    "all"|*)
        if ! run_all_tests; then
            EXIT_CODE=1
        fi
        ;;
esac

# Generate coverage report summary
if [ -f "reports/coverage/all-coverage.xml" ]; then
    echo -e "${YELLOW}Generating coverage summary...${NC}"
    python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('reports/coverage/all-coverage.xml')
    root = tree.getroot()
    coverage = root.attrib.get('line-rate', '0')
    coverage_percent = float(coverage) * 100
    print(f'Overall test coverage: {coverage_percent:.1f}%')
    if coverage_percent < 80:
        print('WARNING: Test coverage is below 80%')
        exit(1)
except Exception as e:
    print(f'Could not parse coverage report: {e}')
"
    COVERAGE_EXIT=$?
    if [ $COVERAGE_EXIT -ne 0 ]; then
        EXIT_CODE=1
    fi
fi

# Performance tests (if available)
if [ -d "tests/performance" ]; then
    echo -e "${YELLOW}Running performance tests...${NC}"
    if ! pytest tests/performance/ -v --tb=short; then
        echo -e "${RED}❌ Performance tests failed${NC}"
        EXIT_CODE=1
    else
        echo -e "${GREEN}✅ Performance tests passed${NC}"
    fi
fi

# Final summary
echo ""
echo -e "${YELLOW}=== TEST SUMMARY ===${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo -e "${YELLOW}Check the reports/ directory for detailed results.${NC}"
fi

exit $EXIT_CODE