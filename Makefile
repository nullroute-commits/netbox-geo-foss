# NetBox Geographic Data Integration Makefile
.PHONY: help build test lint lint-fix format format-check ruff security docker-build clean dev

# Variables
COMPOSE := docker compose -f docker-compose.test.yml

# Help target
help:
	@echo "NetBox Geographic Data Integration"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "All targets run inside Docker containers."
	@echo ""
	@echo "Targets:"
	@echo "  help          Show this help message"
	@echo "  build         Build the dev/test Docker image"
	@echo "  test          Run test suite in Docker"
	@echo "  lint          Run ruff linter in Docker"
	@echo "  lint-fix      Auto-fix ruff lint issues in Docker"
	@echo "  format        Auto-format code with ruff in Docker"
	@echo "  format-check  Check code formatting with ruff in Docker"
	@echo "  ruff          Run full ruff check + format check in Docker"
	@echo "  security      Run security scans in Docker"
	@echo "  docker-build  Build production Docker image"
	@echo "  clean         Clean build artifacts and Docker resources"
	@echo "  dev           Start development environment"

# Build the dev/test image
build:
	@echo "Building dev/test Docker image..."
	$(COMPOSE) build dev

# Run tests in Docker
test: build
	@echo "Running tests in Docker..."
	$(COMPOSE) run --rm test

# Run ruff linter in Docker
lint: build
	@echo "Running ruff linter in Docker..."
	$(COMPOSE) run --rm lint

# Auto-fix ruff lint issues in Docker
lint-fix: build
	@echo "Auto-fixing ruff lint issues in Docker..."
	$(COMPOSE) run --rm dev ruff check --fix src tests

# Check code formatting with ruff in Docker
format-check: build
	@echo "Checking code formatting in Docker..."
	$(COMPOSE) run --rm format-check

# Auto-format code with ruff in Docker
format: build
	@echo "Formatting code in Docker..."
	$(COMPOSE) run --rm format

# Run full ruff check (lint + format check) in Docker
ruff: build
	@echo "Running full ruff check in Docker..."
	$(COMPOSE) run --rm lint
	$(COMPOSE) run --rm format-check

# Run security scans in Docker
security: build
	@echo "Running security scans in Docker..."
	$(COMPOSE) run --rm dev sh -c "bandit -r src -f json -o bandit-report.json || true && safety check || true"

# Build production Docker image
docker-build:
	@echo "Building production Docker image..."
	docker build -t netbox-geo:latest .

# Clean build artifacts and Docker resources
clean:
	@echo "Cleaning up..."
	$(COMPOSE) down -v --rmi local 2>/dev/null || true
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov .ruff_cache
	rm -rf bandit-report.json safety-report.json coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Start development environment
dev:
	@echo "Starting development environment..."
	docker compose up -d
	@echo "Development environment started!"
	@echo "Access the app container with: docker compose exec app bash"