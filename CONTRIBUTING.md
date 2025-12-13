# Contributing to NetBox Geographic Data Integration

Thank you for your interest in contributing to NetBox Geo FOSS! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/netbox-geo-foss.git
   cd netbox-geo-foss
   ```

2. **Set up development environment**
   ```bash
   make setup
   source .venv/bin/activate
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Verify installation**
   ```bash
   make test
   make lint
   ```

## 💻 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Follow our coding standards (see below).

### 3. Run Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_your_module.py

# Run with coverage
pytest --cov=netbox_geo --cov-report=html
```

### 4. Run Linters

```bash
# Check code quality
make lint

# Auto-format code
make format
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Use conventional commit messages:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Build or tooling changes

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 📋 Coding Standards

### Python Style Guide

- **PEP 8 Compliance**: Strictly follow PEP 8
- **Line Length**: Maximum 100 characters
- **Type Hints**: Required for all functions and methods
- **Docstrings**: Google style for all public APIs

Example:

```python
def import_countries(
    source: str,
    batch_size: int = 1000,
    dry_run: bool = False
) -> list[dict[str, Any]]:
    """Import countries from external source.

    Args:
        source: Data source name (e.g., 'geonames', 'naturalearth').
        batch_size: Number of records to process per batch.
        dry_run: If True, preview without making changes.

    Returns:
        List of imported country dictionaries.

    Raises:
        ImportError: If the import operation fails.
        DataValidationError: If country data is invalid.
    """
    pass
```

### Code Quality Requirements

- **Type Coverage**: 100% - All functions must have type hints
- **Test Coverage**: Target >90%
- **Docstring Coverage**: 100% for public APIs
- **Security**: No Bandit high-severity issues
- **Complexity**: Maximum cyclomatic complexity of 12

### Testing Requirements

- Write unit tests for all new functions
- Include integration tests for API interactions
- Add end-to-end tests for complete workflows
- Document test scenarios in docstrings

Example:

```python
def test_rate_limiter_allows_calls_within_limit() -> None:
    """Test that rate limiter allows calls within the configured limit."""
    limiter = RateLimiter(calls_per_minute=60)
    
    # Should allow 10 calls immediately
    for _ in range(10):
        assert limiter.acquire(blocking=False) is True
```

## 🏗️ Architecture Guidelines

### Modularity

- Keep modules focused and single-purpose
- Use dependency injection where appropriate
- Avoid circular dependencies

### Error Handling

- Use custom exceptions from `netbox_geo.core.exceptions`
- Always log errors with context
- Provide helpful error messages

### Configuration

- Use Pydantic v2 for all configuration
- Validate at startup, not runtime
- Support environment variables

### Performance

- Optimize for bulk operations
- Use batch processing for large datasets
- Implement proper rate limiting
- Cache frequently accessed data

## 📝 Documentation

### Code Documentation

- Docstrings for all public functions, classes, and modules
- Google style format
- Include examples for complex functionality

### Project Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for architectural changes
- Add inline comments for complex logic only

## 🔍 Code Review Process

### What We Look For

1. **Functionality**: Does it work as intended?
2. **Tests**: Are there adequate tests?
3. **Code Quality**: Does it follow our standards?
4. **Security**: Are there security implications?
5. **Performance**: Is it optimized appropriately?
6. **Documentation**: Is it well-documented?

### Review Checklist

- [ ] Code follows PEP 8 and type hints are present
- [ ] All tests pass
- [ ] Test coverage is adequate (>90%)
- [ ] Security scans pass
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] No sensitive data in code
- [ ] Performance is acceptable

## 🐛 Reporting Bugs

Use the [Bug Report](https://github.com/nullroute-commits/netbox-geo-foss/issues/new?template=bug_report.md) template and include:

- NetBox version
- netbox-geo version
- Python version
- Steps to reproduce
- Expected vs. actual behavior
- Error messages and logs

## 💡 Feature Requests

Use the [Feature Request](https://github.com/nullroute-commits/netbox-geo-foss/issues/new?template=feature_request.md) template and include:

- Clear description of the feature
- Use case and benefits
- Proposed implementation (optional)
- Alternatives considered

## 🔒 Security Vulnerabilities

**DO NOT** create public issues for security vulnerabilities.

Instead:
1. Use GitHub Security Advisories
2. Or email: security@example.com (if configured)

## 🎯 Development Priorities

### High Priority

- NetBox API compatibility
- Data accuracy and validation
- Performance optimization
- Security hardening

### Medium Priority

- Additional data sources
- Enhanced CLI features
- API endpoint expansion
- Documentation improvements

### Low Priority

- UI/UX enhancements
- Additional export formats
- Third-party integrations

## 📚 Resources

- [NetBox Documentation](https://docs.netbox.dev/)
- [GeoNames Web Services](https://www.geonames.org/export/web-services.html)
- [Natural Earth Data](https://www.naturalearthdata.com/downloads/)
- [OpenStreetMap Wiki](https://wiki.openstreetmap.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Click Documentation](https://click.palletsprojects.com/)

## 📧 Contact

- GitHub Issues: [netbox-geo-foss/issues](https://github.com/nullroute-commits/netbox-geo-foss/issues)
- Discussions: [netbox-geo-foss/discussions](https://github.com/nullroute-commits/netbox-geo-foss/discussions)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
