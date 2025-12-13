#!/bin/bash
# Code quality and linting script
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running code quality checks...${NC}"

# Exit code tracking
EXIT_CODE=0

# Create reports directory
mkdir -p reports

# Black code formatting check
echo -e "${YELLOW}Checking code formatting with Black...${NC}"
if ! black --check --diff app/ config/ --line-length 120; then
    echo -e "${RED}❌ Black formatting check failed${NC}"
    EXIT_CODE=1
else
    echo -e "${GREEN}✅ Black formatting check passed${NC}"
fi

# Flake8 linting
echo -e "${YELLOW}Running Flake8 linting...${NC}"
if ! flake8 app/ config/ --max-line-length=120 --exclude=migrations --statistics --tee --output-file=reports/flake8-report.txt; then
    echo -e "${RED}❌ Flake8 linting failed${NC}"
    EXIT_CODE=1
else
    echo -e "${GREEN}✅ Flake8 linting passed${NC}"
fi

# MyPy type checking
echo -e "${YELLOW}Running MyPy type checking...${NC}"
if ! mypy app/ config/ --ignore-missing-imports --show-error-codes --pretty --html-report reports/mypy-html > reports/mypy-report.txt 2>&1; then
    echo -e "${RED}❌ MyPy type checking failed${NC}"
    cat reports/mypy-report.txt
    EXIT_CODE=1
else
    echo -e "${GREEN}✅ MyPy type checking passed${NC}"
fi

# Bandit security linting
echo -e "${YELLOW}Running Bandit security checks...${NC}"
if ! bandit -r app/ -f json -o reports/bandit-report.json; then
    echo -e "${RED}❌ Bandit security checks failed${NC}"
    EXIT_CODE=1
else
    echo -e "${GREEN}✅ Bandit security checks passed${NC}"
fi

# Safety dependency vulnerability check
echo -e "${YELLOW}Checking dependencies for vulnerabilities...${NC}"
if ! safety check -r requirements/base.txt --json --output reports/safety-report.json; then
    echo -e "${RED}❌ Safety vulnerability check failed${NC}"
    EXIT_CODE=1
else
    echo -e "${GREEN}✅ Safety vulnerability check passed${NC}"
fi

# Complexity analysis with radon
echo -e "${YELLOW}Analyzing code complexity...${NC}"
if command -v radon >/dev/null 2>&1; then
    radon cc app/ --json > reports/complexity-report.json
    radon mi app/ --json > reports/maintainability-report.json
    echo -e "${GREEN}✅ Complexity analysis completed${NC}"
else
    echo -e "${YELLOW}⚠️ Radon not installed, skipping complexity analysis${NC}"
fi

# Import sorting check
echo -e "${YELLOW}Checking import sorting with isort...${NC}"
if command -v isort >/dev/null 2>&1; then
    if ! isort --check-only --diff app/ config/; then
        echo -e "${RED}❌ Import sorting check failed${NC}"
        EXIT_CODE=1
    else
        echo -e "${GREEN}✅ Import sorting check passed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ isort not installed, skipping import sorting check${NC}"
fi

# Final summary
echo ""
echo -e "${YELLOW}=== CODE QUALITY SUMMARY ===${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All code quality checks passed!${NC}"
else
    echo -e "${RED}❌ Some code quality checks failed!${NC}"
    echo -e "${YELLOW}Check the reports/ directory for detailed results.${NC}"
fi

exit $EXIT_CODE