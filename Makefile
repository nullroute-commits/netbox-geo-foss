# Enterprise CI/CD Pipeline Makefile
.PHONY: help build test lint security deploy clean

# Variables
ENVIRONMENT ?= dev
BUILD_ID ?= $(shell date +%Y%m%d%H%M%S)
COMMIT_SHA ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
DOCKER_COMPOSE = docker compose
PIPELINE_COMPOSE = $(DOCKER_COMPOSE) -f docker-compose.pipeline.yml

# Help target
help:
	@echo "Enterprise CI/CD Pipeline"
	@echo ""
	@echo "Usage: make [target] [ENVIRONMENT=dev|test|staging|prod]"
	@echo ""
	@echo "Targets:"
	@echo "  help          Show this help message"
	@echo "  setup         Set up CI/CD infrastructure"
	@echo "  test          Run all tests"
	@echo "  lint          Run code quality checks"
	@echo "  security      Run security scans"
	@echo "  build         Build Docker images"
	@echo "  deploy        Deploy to environment"
	@echo "  pipeline      Run full CI/CD pipeline"
	@echo "  clean         Clean up resources"
	@echo ""
	@echo "CI/CD Infrastructure:"
	@echo "  ci-up         Start CI/CD services"
	@echo "  ci-down       Stop CI/CD services"
	@echo "  ci-logs       Show CI/CD logs"
	@echo ""
	@echo "Environment-specific targets:"
	@echo "  dev-up        Start development environment"
	@echo "  test-up       Start test environment"
	@echo "  prod-up       Start production environment"

# Setup CI/CD infrastructure
setup:
	@echo "Setting up CI/CD infrastructure..."
	$(DOCKER_COMPOSE) -f docker-compose.ci.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 30
	@echo "CI/CD infrastructure is ready!"

# Run tests using pipeline executor
test:
	@echo "Running tests in pipeline..."
	$(PIPELINE_COMPOSE) run --rm \
		-e ENVIRONMENT=$(ENVIRONMENT) \
		-e BUILD_ID=$(BUILD_ID) \
		-e COMMIT_SHA=$(COMMIT_SHA) \
		-e PIPELINE_COMMAND=test \
		pipeline-executor test

# Run linting
lint:
	@echo "Running code quality checks..."
	$(PIPELINE_COMPOSE) run --rm \
		-e ENVIRONMENT=$(ENVIRONMENT) \
		-e BUILD_ID=$(BUILD_ID) \
		-e COMMIT_SHA=$(COMMIT_SHA) \
		-e PIPELINE_COMMAND=lint \
		pipeline-executor lint

# Run security scans
security:
	@echo "Running security scans..."
	$(PIPELINE_COMPOSE) run --rm \
		-e ENVIRONMENT=$(ENVIRONMENT) \
		-e BUILD_ID=$(BUILD_ID) \
		-e COMMIT_SHA=$(COMMIT_SHA) \
		-e PIPELINE_COMMAND=security \
		pipeline-executor security

# Build Docker images
build:
	@echo "Building Docker images..."
	$(PIPELINE_COMPOSE) run --rm \
		-e ENVIRONMENT=$(ENVIRONMENT) \
		-e BUILD_ID=$(BUILD_ID) \
		-e COMMIT_SHA=$(COMMIT_SHA) \
		-e PIPELINE_COMMAND=build \
		pipeline-executor build

# Deploy to environment
deploy:
	@echo "Deploying to $(ENVIRONMENT) environment..."
	$(PIPELINE_COMPOSE) run --rm \
		-e ENVIRONMENT=$(ENVIRONMENT) \
		-e BUILD_ID=$(BUILD_ID) \
		-e COMMIT_SHA=$(COMMIT_SHA) \
		-e PIPELINE_COMMAND=deploy \
		pipeline-executor deploy

# Run full pipeline
pipeline: lint test build security
	@echo "Full pipeline completed successfully!"

# CI/CD infrastructure management
ci-up:
	$(DOCKER_COMPOSE) -f docker-compose.ci.yml up -d

ci-down:
	$(DOCKER_COMPOSE) -f docker-compose.ci.yml down

ci-logs:
	$(DOCKER_COMPOSE) -f docker-compose.ci.yml logs -f

ci-restart:
	$(DOCKER_COMPOSE) -f docker-compose.ci.yml restart

# Environment-specific targets
dev-up:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.dev.yml up -d

dev-down:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.dev.yml down

dev-logs:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.dev.yml logs -f

test-up:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.test.yml up -d

test-down:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.test.yml down

prod-up:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.prod.yml up -d

prod-down:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.prod.yml down

# Clean up
clean:
	@echo "Cleaning up..."
	$(PIPELINE_COMPOSE) down -v
	$(DOCKER_COMPOSE) -f docker-compose.ci.yml down -v
	docker system prune -af --volumes
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov coverage.xml .coverage

# Docker compose shortcuts
ps:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.$(ENVIRONMENT).yml ps

logs:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.$(ENVIRONMENT).yml logs -f

shell:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.$(ENVIRONMENT).yml exec app bash

# Database management
db-migrate:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.$(ENVIRONMENT).yml \
		exec app alembic upgrade head

db-rollback:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.$(ENVIRONMENT).yml \
		exec app alembic downgrade -1

db-reset:
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.$(ENVIRONMENT).yml \
		exec app alembic downgrade base && \
	$(DOCKER_COMPOSE) -f docker-compose.base.yml -f docker-compose.$(ENVIRONMENT).yml \
		exec app alembic upgrade head