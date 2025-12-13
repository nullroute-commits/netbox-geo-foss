# Enterprise CI/CD Pipeline

A production-grade CI/CD pipeline implementation using Python 3.13, Docker Compose, and Ansible with comprehensive testing, security scanning, and multi-environment deployment support.

## 🚀 Features

- **Python 3.13.0** (latest stable) with modern async/await patterns and type hints
- **Docker Compose** for consistent environment management
- **Multi-environment support** (dev, test, staging, prod) with PATH-scoped configurations
- **Comprehensive CI/CD** with GitHub Actions, GitLab CI, and Jenkins support
- **Infrastructure as Code** using Ansible 10.5.0 (latest stable)
- **Security-first approach** with automated scanning and policy enforcement
- **Enterprise-grade monitoring** with Prometheus, Grafana, and distributed tracing
- **Automated testing** including unit, integration, E2E, and performance tests
- **Blue-green and rolling deployments** with automatic rollback capabilities

## 📋 Prerequisites

- Docker Engine 27.2.0+ and Docker Compose v2.29.2+
- Python 3.13.0
- Ansible 10.5.0 (ansible-core 2.17.5)
- Make (for automation)
- Git

## 🏗️ Project Structure

```
enterprise-app/
├── src/                    # Application source code
│   ├── api/               # FastAPI application
│   ├── core/              # Core business logic
│   └── utils/             # Utility functions
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── performance/       # Performance tests
├── docker/                 # Docker configurations
│   ├── dev/               # Development environment
│   ├── test/              # Test environment
│   └── prod/              # Production environment
├── environments/           # Environment-specific configs
│   ├── dev/               # Development configs with PATH scoping
│   ├── test/              # Test configs
│   └── prod/              # Production configs
├── ansible/                # Ansible automation
│   ├── playbooks/         # Deployment playbooks
│   ├── inventories/       # Environment inventories
│   └── roles/             # Reusable roles
├── ci-cd/                  # CI/CD configurations
│   ├── github-actions/    # GitHub Actions workflows
│   └── gitlab-ci/         # GitLab CI templates
└── monitoring/            # Monitoring configurations
    ├── prometheus/        # Prometheus configs
    └── grafana/           # Grafana dashboards
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/enterprise-app.git
cd enterprise-app
```

### 2. Set Up Environment

```bash
# Copy environment templates
cp environments/dev/.env.example environments/dev/.env.local

# Load environment (with PATH scoping)
source scripts/env-loader.sh dev
```

### 3. Start Development Environment

```bash
# Using Make
make dev-up

# Or using Docker Compose directly
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml up -d
```

### 4. Run Tests

```bash
# Run all tests
make test

# Run specific test suites
make test ENVIRONMENT=test
docker compose -f docker-compose.pipeline.yml run --rm pipeline-executor test
```

## 🔧 Configuration

### Environment Variables

Environment-specific configurations are stored in `environments/{env}/.env` files with PATH scoping support:

```bash
# Load environment with PATH scoping
source scripts/env-loader.sh [dev|test|staging|prod]

# This sets:
# - PATH to include environment-specific binaries
# - PYTHONPATH for environment-specific modules
# - Environment-specific tool configurations
```

### Docker Compose Environments

Each environment has its own Docker Compose configuration:

- `docker-compose.dev.yml` - Development with hot-reload and debug tools
- `docker-compose.test.yml` - Testing with isolated databases
- `docker-compose.prod.yml` - Production with security and monitoring

## 📦 CI/CD Pipeline

### Using Docker Compose for CI/CD Runners

The pipeline uses Docker Compose to run CI/CD jobs consistently:

```bash
# Start CI/CD infrastructure
make setup

# Run pipeline stages
make pipeline ENVIRONMENT=test
```

### Pipeline Stages

1. **Code Quality** - Linting, formatting, type checking
2. **Security Scanning** - Dependency scanning, SAST, container scanning
3. **Testing** - Unit, integration, and E2E tests
4. **Build** - Multi-stage Docker builds
5. **Deploy** - Environment-specific deployment with Ansible

### GitHub Actions

```yaml
name: CI/CD Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: [self-hosted, docker]
    steps:
      - uses: actions/checkout@v4
      - run: make test
```

### GitLab CI

```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - make test
```

## 🔒 Security

### Security Scanning Tools

- **Bandit** - Python AST security scanner
- **Safety** - Dependency vulnerability scanner
- **Trivy** - Container vulnerability scanner
- **SonarQube** - Code quality and security analysis

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🚀 Deployment

### Deploy to Environment

```bash
# Deploy to development
make deploy ENVIRONMENT=dev

# Deploy to production (requires confirmation)
environments/prod/bin/deploy --confirm-production
```

### Using Ansible

```bash
# Deploy with Ansible
ansible-playbook -i ansible/inventories/prod/hosts.yml \
  ansible/playbooks/deploy.yml \
  -e "app_version=v1.0.0" \
  -e "environment=production"
```

### Rollback

```bash
# Rollback to previous version
ansible-playbook -i ansible/inventories/prod/hosts.yml \
  ansible/playbooks/rollback.yml \
  -e "rollback_version=v0.9.0" \
  -e "environment=production"
```

## 📊 Monitoring

### Access Monitoring Tools

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Jaeger**: http://localhost:16686

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics
```

## 🧪 Testing

### Run Test Suites

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# End-to-end tests
pytest tests/e2e -v

# Performance tests
docker run --rm -v ./tests/performance:/scripts \
  grafana/k6:latest run /scripts/load-test.js
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run application locally
uvicorn src.api.main:app --reload

# Run with Docker
docker compose -f docker-compose.dev.yml up
```

### Code Style

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

## 📚 Documentation

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Generate Documentation

```bash
# Build documentation
mkdocs build

# Serve locally
mkdocs serve
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with modern Python 3.13.0 features
- Uses latest Ansible 10.5.0 for infrastructure automation
- Implements enterprise best practices for CI/CD
- Docker Compose for consistent environments across all stages

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/enterprise-app/issues)
- **Email**: support@example.com
- **Slack**: [#enterprise-app](https://slack.example.com)

---

**Note**: This is a reference implementation demonstrating enterprise-grade CI/CD practices. Adapt the configuration to match your specific requirements and infrastructure.