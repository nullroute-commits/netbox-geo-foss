# NetBox Geographic Data Integration Makefile
.PHONY: help setup test lint format security docker-build clean

# Variables
PYTHON := python3.13
VENV := .venv
BIN := $(VENV)/bin
PYTHON_BIN := $(BIN)/python
PIP := $(BIN)/pip

# Help target
help:
	@echo "NetBox Geographic Data Integration"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help          Show this help message"
	@echo "  setup         Create venv and install dependencies"
	@echo "  test          Run test suite"
	@echo "  lint          Run all linters"
	@echo "  format        Auto-format code"
	@echo "  security      Run security scans"
	@echo "  docker-build  Build Docker image"
	@echo "  clean         Clean build artifacts"
	@echo "  run           Run CLI help"
	@echo "  dev           Start development environment"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements/dev.txt
	$(PIP) install -e .
	@echo "Development environment ready!"
	@echo "Activate with: source $(VENV)/bin/activate"

# Run tests
test:
	@echo "Running tests..."
	$(BIN)/pytest --cov=netbox_geo --cov-report=html --cov-report=term-missing

# Run all linters
lint:
	@echo "Running linters..."
	$(BIN)/black --check src tests
	$(BIN)/flake8 src tests
	$(BIN)/isort --check-only src tests
	$(BIN)/mypy src

# Auto-format code
format:
	@echo "Formatting code..."
	$(BIN)/black src tests
	$(BIN)/isort src tests

# Run security scans
security:
	@echo "Running security scans..."
	$(BIN)/bandit -r src -f json -o bandit-report.json || true
	$(BIN)/safety check || true

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t netbox-geo:latest .

# Clean build artifacts
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV)
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov
	rm -rf bandit-report.json safety-report.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run CLI
run:
	@echo "Running netbox-geo CLI..."
	$(BIN)/netbox-geo --help

# Start development environment
dev:
	@echo "Starting development environment..."
	docker compose up -d
	@echo "Development environment started!"
	@echo "Access the app container with: docker compose exec app bash"