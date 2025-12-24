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

- [Architecture Overview](ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [API Documentation](https://netbox-geo-foss.readthedocs.io)

## 🐛 Reporting Issues

Please use [GitHub Issues](https://github.com/nullroute-commits/netbox-geo-foss/issues) with appropriate templates:
- Bug Report
- Feature Request
- Security Report (for vulnerabilities)