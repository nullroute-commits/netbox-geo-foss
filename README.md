# NetBox Geographic Data Integration - FOSS Edition

[![CI Pipeline](https://github.com/nullroute-commits/netbox-geo-foss/actions/workflows/ci.yml/badge.svg)](https://github.com/nullroute-commits/netbox-geo-foss/actions/workflows/ci.yml)
[![Python 3.13.1](https://img.shields.io/badge/python-3.13.1-blue.svg)](https://www.python.org/downloads/release/python-3131/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Enterprise-grade integration of open-source geographic data (GeoNames, Natural Earth, OpenStreetMap) with NetBox 4.4.8+.

## 🌍 Overview

NetBox Geo FOSS provides a production-ready solution for importing and synchronizing geographic data from multiple FOSS sources into NetBox. Designed for network automation workflows and optimized for bulk operations (100k+ records).

### Key Features

- **Multi-Source Integration**: GeoNames, Natural Earth, and OpenStreetMap
- **NetBox 4.4.8+ Compatible**: Full API integration with pynetbox 7.5.0
- **Production-Ready**: Rate limiting, retry logic, bulk operations
- **Type-Safe**: Full type hints and Pydantic v2 validation
- **Enterprise Quality**: Comprehensive logging, monitoring hooks, error handling
- **CLI & API**: Click-based CLI and REST API
- **Docker Support**: Multi-stage builds with Python 3.13.1
- **Tested**: >90% code coverage target

## 📋 Prerequisites

- Python 3.13.1+
- NetBox 4.4.8+
- PostgreSQL 17+ (for local caching)
- Docker & Docker Compose (optional)
- GeoNames account (free registration)

## 🚀 Quick Start

### Installation via pip

```bash
pip install netbox-geo-foss
```

### Installation from source

```bash
git clone https://github.com/nullroute-commits/netbox-geo-foss.git
cd netbox-geo-foss
make setup
source .venv/bin/activate
```

### Docker

```bash
docker compose up -d
docker compose exec app netbox-geo --help
```

## ⚙️ Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# NetBox Configuration
NETBOX_URL=https://netbox.example.com
NETBOX_TOKEN=your_api_token_here

# GeoNames Configuration
GEONAMES_USERNAME=your_geonames_username

# Data Management
DATA_BATCH_SIZE=1000
DATA_MIN_CITY_POPULATION=15000
```

## 💻 Usage

### Import Geographic Data

```bash
# Import from all sources
netbox-geo import --source all

# Import from specific source
netbox-geo import --source geonames

# Dry run (preview without changes)
netbox-geo import --source geonames --dry-run
```

### Synchronize with NetBox

```bash
# Sync all data
netbox-geo sync

# Force full sync
netbox-geo sync --force
```

### Validate Data

```bash
# Validate all data
netbox-geo validate --source all

# Validate NetBox data only
netbox-geo validate --source netbox
```

### Configuration Management

```bash
# Show current configuration
netbox-geo config --show

# Test NetBox connectivity
netbox-geo config --test
```

## 🏗️ Architecture

```
netbox-geo-foss/
├── src/netbox_geo/
│   ├── core/              # Configuration, exceptions
│   ├── models/            # Data models
│   ├── importers/         # Data source importers
│   ├── netbox/            # NetBox API client
│   ├── database/          # Local database models
│   ├── cache/             # Caching utilities
│   ├── utils/             # Helper functions
│   ├── cli/               # Command-line interface
│   └── api/               # REST API
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── performance/       # Performance tests
└── docs/                  # Documentation
```

### Core Components

- **NetBox Client**: Rate-limited API client with retry logic and bulk operations
- **Data Importers**: Pluggable importers for each geographic data source
- **Configuration System**: Pydantic v2-based configuration with environment validation
- **Rate Limiter**: Token bucket algorithm for API protection
- **CLI**: Rich terminal interface with Click

## 🔧 Development

### Setup Development Environment

```bash
make setup
source .venv/bin/activate
```

### Run Tests

```bash
make test
```

### Code Quality

```bash
# Run all linters
make lint

# Auto-format code
make format

# Security scans
make security
```

### Docker Build

```bash
make docker-build
```

## 📊 Performance Considerations

- Optimized for bulk operations (100k+ records)
- Configurable batch sizes
- Rate limiting to protect NetBox API
- Efficient caching of geographic data
- Async operations support

## 🔒 Security

- No credentials in code
- Environment-based configuration
- Rate limiting protection
- Input validation with Pydantic
- Regular security scans (Bandit, Safety)
- CodeQL analysis

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and pull request process.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [NetBox](https://github.com/netbox-community/netbox) - Network infrastructure management
- [GeoNames](https://www.geonames.org/) - Geographic database
- [Natural Earth](https://www.naturalearthdata.com/) - Public domain map dataset
- [OpenStreetMap](https://www.openstreetmap.org/) - Collaborative map data

## 📚 Documentation

- [Architecture Overview](docs/analysis/ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [API Documentation](https://netbox-geo-foss.readthedocs.io)

## 🐛 Reporting Issues

Please use [GitHub Issues](https://github.com/nullroute-commits/netbox-geo-foss/issues) with appropriate templates:
- Bug Report
- Feature Request
- Security Report (for vulnerabilities)
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