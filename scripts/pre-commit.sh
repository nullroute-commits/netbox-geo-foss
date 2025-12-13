#!/bin/bash
# Pre-commit hook script
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running pre-commit checks...${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check for Python virtual environment
if [ -z "$VIRTUAL_ENV" ] && [ ! -f ".venv/bin/activate" ]; then
    echo -e "${YELLOW}⚠️ No Python virtual environment detected${NC}"
    echo -e "${YELLOW}Consider using a virtual environment for development${NC}"
fi

# Install development dependencies if needed
if ! python -c "import black" 2>/dev/null; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    pip install -r requirements/development.txt
fi

# Format code with Black
echo -e "${YELLOW}Formatting code with Black...${NC}"
if ! black app/ config/ --line-length 120; then
    echo -e "${RED}❌ Black formatting failed${NC}"
    exit 1
fi

# Sort imports with isort
if command -v isort >/dev/null 2>&1; then
    echo -e "${YELLOW}Sorting imports with isort...${NC}"
    isort app/ config/
fi

# Lint with Flake8
echo -e "${YELLOW}Linting with Flake8...${NC}"
if ! flake8 app/ config/ --max-line-length=120 --exclude=migrations; then
    echo -e "${RED}❌ Flake8 linting failed${NC}"
    exit 1
fi

# Type checking with MyPy
echo -e "${YELLOW}Type checking with MyPy...${NC}"
if ! mypy app/ config/ --ignore-missing-imports; then
    echo -e "${RED}❌ MyPy type checking failed${NC}"
    exit 1
fi

# Check for secrets
echo -e "${YELLOW}Checking for secrets...${NC}"
if git diff --cached --name-only | xargs grep -l "password\|secret\|key" | grep -v ".example" | grep -v "requirements"; then
    echo -e "${RED}❌ Potential secrets found in staged files${NC}"
    echo -e "${YELLOW}Please review and remove any sensitive information${NC}"
    exit 1
fi

# Run quick tests
echo -e "${YELLOW}Running quick tests...${NC}"
if [ -f "manage.py" ]; then
    if ! python manage.py check; then
        echo -e "${RED}❌ Django check failed${NC}"
        exit 1
    fi
fi

# Add formatted files to git
git add -u

echo -e "${GREEN}✅ All pre-commit checks passed!${NC}"