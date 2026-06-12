#!/bin/bash
# Code quality checks – black / flake8 / isort / mypy
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${GREEN}Running code quality checks...${NC}"
mkdir -p reports
EXIT=0

run() {
    local name=$1; shift
    echo -e "${YELLOW}→ $name${NC}"
    if "$@"; then
        echo -e "${GREEN}  ✓ $name passed${NC}"
    else
        echo -e "${RED}  ✗ $name failed${NC}"
        EXIT=1
    fi
}

run "black"  black --check src tests
run "flake8" flake8 src tests
run "isort"  isort --check-only src tests
run "mypy"   mypy src --show-error-codes

echo ""
if [ $EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ All quality checks passed${NC}"
else
    echo -e "${RED}✗ Quality checks failed – see output above${NC}"
fi
exit $EXIT
