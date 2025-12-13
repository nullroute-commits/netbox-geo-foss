#!/bin/bash
set -e

# Pipeline executor entrypoint script
echo "Starting pipeline executor for environment: ${ENVIRONMENT}"
echo "Build ID: ${BUILD_ID}"
echo "Commit SHA: ${COMMIT_SHA}"

# Function to run tests
run_tests() {
    echo "Running tests..."
    
    # Set up environment
    export DATABASE_URL="postgresql://pipeline_user:pipeline_password@test-db:5432/pipeline_test"
    export REDIS_URL="redis://test-cache:6379/0"
    
    # Wait for services
    echo "Waiting for services..."
    until pg_isready -h test-db -U pipeline_user; do
        echo "Waiting for PostgreSQL..."
        sleep 2
    done
    
    until redis-cli -h test-cache ping; do
        echo "Waiting for Redis..."
        sleep 2
    done
    
    # Run database migrations
    echo "Running database migrations..."
    alembic upgrade head
    
    # Run tests
    echo "Running unit tests..."
    pytest tests/unit \
        --cov=src \
        --cov-report=xml:/artifacts/coverage.xml \
        --cov-report=html:/artifacts/htmlcov \
        --junitxml=/artifacts/junit.xml
    
    echo "Running integration tests..."
    pytest tests/integration -v
}

# Function to run linting
run_lint() {
    echo "Running code quality checks..."
    
    # Format check
    black --check src tests
    
    # Linting
    ruff check src tests
    
    # Type checking
    mypy src
    
    # Security checks
    bandit -r src -f json -o /artifacts/bandit-report.json
    safety check --json > /artifacts/safety-report.json
    pip-audit --desc --format json > /artifacts/pip-audit-report.json
}

# Function to build image
run_build() {
    echo "Building Docker image..."
    
    docker build \
        -t enterprise-app:${COMMIT_SHA} \
        -t enterprise-app:${ENVIRONMENT} \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VERSION=${COMMIT_SHA} \
        --build-arg VCS_REF=${COMMIT_SHA} \
        .
    
    # Save image metadata
    docker inspect enterprise-app:${COMMIT_SHA} > /artifacts/image-metadata.json
}

# Function to run security scan
run_security() {
    echo "Running security scans..."
    
    # Scan dependencies
    safety check --json > /artifacts/safety-scan.json
    
    # Scan code
    bandit -r src -f json -o /artifacts/bandit-scan.json
    
    # Scan Docker image
    if docker image inspect enterprise-app:${COMMIT_SHA} >/dev/null 2>&1; then
        trivy image \
            --format json \
            --output /artifacts/trivy-scan.json \
            enterprise-app:${COMMIT_SHA}
    fi
}

# Function to deploy
run_deploy() {
    echo "Running deployment for environment: ${ENVIRONMENT}"
    
    # Validate environment
    case ${ENVIRONMENT} in
        dev|test|staging|prod)
            ;;
        *)
            echo "Invalid environment: ${ENVIRONMENT}"
            exit 1
            ;;
    esac
    
    # Run Ansible deployment
    ansible-playbook \
        -i /workspace/ansible/inventories/${ENVIRONMENT}/hosts.yml \
        /workspace/ansible/playbooks/deploy.yml \
        -e "app_version=${COMMIT_SHA}" \
        -e "environment=${ENVIRONMENT}" \
        -e "build_id=${BUILD_ID}"
}

# Main execution
case ${1:-test} in
    test)
        run_tests
        ;;
    lint)
        run_lint
        ;;
    build)
        run_build
        ;;
    security)
        run_security
        ;;
    deploy)
        run_deploy
        ;;
    all)
        run_lint
        run_tests
        run_build
        run_security
        ;;
    *)
        echo "Unknown command: $1"
        echo "Available commands: test, lint, build, security, deploy, all"
        exit 1
        ;;
esac

echo "Pipeline execution completed successfully!"