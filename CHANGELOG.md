# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-14

### Added
- Initial release of NetBox Geographic Data Integration - FOSS Edition
- Multi-source geographic data integration (GeoNames, Natural Earth, OpenStreetMap)
- NetBox 4.4.8+ API client with rate limiting and retry logic
- Click-based CLI interface with rich terminal output
- REST API with FastAPI
- Type-safe configuration with Pydantic v2
- Docker support with multi-stage builds
- Comprehensive test suite with pytest
- Code quality tools (black, flake8, isort, mypy)
- Security scanning (bandit, safety, CodeQL)
- CI/CD pipelines for GitHub Actions

### Changed
- Updated Python version requirement to 3.12+ (from 3.13.1)
- Migrated from deprecated Pydantic v1 `env` parameter to automatic environment mapping
- Updated SQLAlchemy imports to use modern declarative_base location
- Fixed database engine initialization for SQLite compatibility

### Fixed
- GitHub Actions workflows now use Python 3.12 consistently across all jobs
- Replaced deprecated `actions/create-release@v1` with `softprops/action-gh-release@v2`
- Updated ci-cd.yml to use `ubuntu-latest` runners instead of self-hosted
- Fixed flake8 violations in docstrings
- Resolved Pydantic v2 deprecation warnings
- Fixed SQLAlchemy deprecation warnings
- Corrected database configuration for both PostgreSQL and SQLite

### Security
- Implemented rate limiting for API protection
- Added environment-based configuration (no credentials in code)
- Input validation with Pydantic
- Regular security scans integrated in CI/CD
- CodeQL analysis for code security

## [Unreleased]

### Planned
- Integration tests with live NetBox instance
- Additional data sources
- Performance optimizations for bulk operations
- Extended CLI commands
- Web UI for data management
