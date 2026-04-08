# Configuration System Documentation

This document describes the configuration management system for the Django 5 Multi-Architecture CI/CD Pipeline application.

**Last updated:** 2025-08-30 22:40:55 UTC by nullroute-commits

## Table of Contents

- [Overview](#overview)
- [Configuration Hierarchy](#configuration-hierarchy)
- [Environment Management](#environment-management)
- [Settings Structure](#settings-structure)
- [Security Configuration](#security-configuration)
- [Runtime Configuration](#runtime-configuration)
- [Configuration Validation](#configuration-validation)
- [Best Practices](#best-practices)

## Overview

The configuration system is designed to support multiple environments with secure, maintainable, and flexible configuration management. It follows the twelve-factor app methodology for configuration.

### Key Principles

- **Environment Separation:** Clear separation between environments
- **Security First:** Sensitive data properly protected
- **Immutable Infrastructure:** Configuration via environment variables
- **Validation:** Configuration validation at startup
- **Documentation:** Self-documenting configuration

## Configuration Hierarchy

### Configuration Precedence

```
1. Environment Variables (Highest Priority)
2. Environment-specific settings files
3. Base settings file
4. Default values (Lowest Priority)
```

### File Structure

```
config/
├── settings/
│   ├── __init__.py
│   ├── base.py              # Common settings
│   ├── development.py       # Development overrides
│   ├── testing.py          # Testing overrides
│   └── production.py       # Production overrides
├── urls.py
└── wsgi.py

environments/
├── .env.development.example
├── .env.testing.example
└── .env.production.example

# Root-level environment files
.env.example                 # Main environment template
.env.app.example            # Application-specific settings
.env.db.example             # Database configuration
.env.cache.example          # Cache configuration
.env.queue.example          # Queue configuration
.env.security.example       # Security settings
.env.logging.example        # Logging configuration
```

## Environment Management

### Environment Detection

```python
# config/settings/__init__.py
import os

# Determine environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
DJANGO_SETTINGS_MODULE = os.environ.get(
    'DJANGO_SETTINGS_MODULE', 
    f'config.settings.{ENVIRONMENT}'
)

# Import appropriate settings
if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'testing':
    from .testing import *
else:
    from .development import *
```

### Environment Variables

```python
# Utility functions for environment variables
import os
from typing import Union, List, Dict, Any

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    return os.environ.get(key, str(default)).lower() in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable."""
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float environment variable."""
    try:
        return float(os.environ.get(key, str(default)))
    except ValueError:
        return default

def get_env_list(key: str, default: List[str] = None, separator: str = ',') -> List[str]:
    """Get list environment variable."""
    if default is None:
        default = []
    
    value = os.environ.get(key, '')
    if not value:
        return default
    
    return [item.strip() for item in value.split(separator) if item.strip()]

def get_env_dict(key: str, default: Dict[str, str] = None) -> Dict[str, str]:
    """Get dictionary environment variable (JSON format)."""
    import json
    
    if default is None:
        default = {}
    
    value = os.environ.get(key, '')
    if not value:
        return default
    
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default
```

## Settings Structure

### Base Settings

```python
# config/settings/base.py
import os
import sys
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'app'))

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = []

LOCAL_APPS = [
    'app',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL configuration
ROOT_URLCONF = 'config.urls'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'config.wsgi.application'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = get_env_bool('USE_TZ', True)

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

### Database Configuration

```python
# Database configuration with environment variables
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('POSTGRES_DB', 'django_app'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': get_env_int('POSTGRES_PORT', 5432),
        'CONN_MAX_AGE': get_env_int('DATABASE_CONN_MAX_AGE', 600),
        'CONN_HEALTH_CHECKS': get_env_bool('DATABASE_CONN_HEALTH_CHECKS', True),
        'OPTIONS': {
            'sslmode': os.environ.get('DATABASE_SSL_MODE', 'prefer'),
        },
    }
}

# Read replica configuration (if available)
if os.environ.get('READ_REPLICA_HOST'):
    DATABASES['read_replica'] = {
        'ENGINE': DATABASES['default']['ENGINE'],
        'NAME': DATABASES['default']['NAME'],
        'USER': os.environ.get('READ_REPLICA_USER', DATABASES['default']['USER']),
        'PASSWORD': os.environ.get('READ_REPLICA_PASSWORD', DATABASES['default']['PASSWORD']),
        'HOST': os.environ.get('READ_REPLICA_HOST'),
        'PORT': get_env_int('READ_REPLICA_PORT', 5432),
        'CONN_MAX_AGE': DATABASES['default']['CONN_MAX_AGE'],
        'OPTIONS': DATABASES['default']['OPTIONS'],
    }
```

### Cache Configuration

```python
# Cache configuration with Memcached
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': get_env_list('MEMCACHED_SERVERS', ['memcached:11211']),
        'KEY_PREFIX': os.environ.get('CACHE_KEY_PREFIX', 'app'),
        'VERSION': get_env_int('CACHE_VERSION', 1),
        'TIMEOUT': get_env_int('CACHE_DEFAULT_TIMEOUT', 300),
        'OPTIONS': {
            'no_delay': True,
            'connect_timeout': 1,
            'timeout': get_env_float('MEMCACHED_SOCKET_TIMEOUT', 3.0),
            'max_pool_size': get_env_int('MEMCACHED_MAX_POOL_SIZE', 10),
        }
    }
}

# Session cache (separate from default cache)
if os.environ.get('SESSION_CACHE_LOCATION'):
    CACHES['sessions'] = {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': get_env_list('SESSION_CACHE_LOCATION'),
        'KEY_PREFIX': 'sessions',
        'TIMEOUT': get_env_int('SESSION_CACHE_TIMEOUT', 86400),
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'sessions'
```

### Queue Configuration

```python
# RabbitMQ configuration
RABBITMQ_CONFIG = {
    'HOST': os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
    'PORT': get_env_int('RABBITMQ_PORT', 5672),
    'USERNAME': os.environ.get('RABBITMQ_USERNAME', 'guest'),
    'PASSWORD': os.environ.get('RABBITMQ_PASSWORD', 'guest'),
    'VHOST': os.environ.get('RABBITMQ_VHOST', '/'),
    'EXCHANGE': os.environ.get('RABBITMQ_EXCHANGE', 'app.topic'),
    'HEARTBEAT': get_env_int('RABBITMQ_HEARTBEAT', 60),
    'BLOCKED_TIMEOUT': get_env_int('RABBITMQ_BLOCKED_TIMEOUT', 300),
    'PREFETCH_COUNT': get_env_int('RABBITMQ_PREFETCH_COUNT', 10),
}
```

## Security Configuration

### Security Settings

```python
# Security configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')

# Security middleware settings
SECURE_SSL_REDIRECT = get_env_bool('SECURE_SSL_REDIRECT', False)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = get_env_int('SECURE_HSTS_SECONDS', 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
SECURE_HSTS_PRELOAD = get_env_bool('SECURE_HSTS_PRELOAD', True)

# Session security
SESSION_COOKIE_SECURE = get_env_bool('SESSION_COOKIE_SECURE', False)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = get_env_int('SESSION_COOKIE_AGE', 86400)
SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Strict')

# CSRF protection
CSRF_COOKIE_SECURE = get_env_bool('CSRF_COOKIE_SECURE', False)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = os.environ.get('CSRF_COOKIE_SAMESITE', 'Strict')
CSRF_TRUSTED_ORIGINS = get_env_list('CSRF_TRUSTED_ORIGINS', [])

# Content Security Policy
CSP_DEFAULT_SRC = get_env_list('CSP_DEFAULT_SRC', ["'self'"])
CSP_SCRIPT_SRC = get_env_list('CSP_SCRIPT_SRC', ["'self'", "'unsafe-inline'"])
CSP_STYLE_SRC = get_env_list('CSP_STYLE_SRC', ["'self'", "'unsafe-inline'"])
CSP_IMG_SRC = get_env_list('CSP_IMG_SRC', ["'self'", "data:", "https:"])
```

### Secrets Management

```python
# Secrets loading from files (Docker secrets)
def load_secret(secret_name: str, default: str = '') -> str:
    """Load secret from file or environment variable."""
    secret_file = f'/run/secrets/{secret_name}'
    env_var = f'{secret_name.upper()}_FILE'
    
    # Try to load from Docker secret file
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    
    # Try to load from environment variable pointing to file
    file_path = os.environ.get(env_var)
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read().strip()
    
    # Fall back to environment variable
    return os.environ.get(secret_name, default)

# Load secrets
SECRET_KEY = load_secret('SECRET_KEY', 'change-me-in-production')
DATABASES['default']['PASSWORD'] = load_secret('POSTGRES_PASSWORD', '')
RABBITMQ_CONFIG['PASSWORD'] = load_secret('RABBITMQ_PASSWORD', 'guest')
```

## Runtime Configuration

### Dynamic Configuration

```python
# SystemConfiguration model for runtime settings
class RuntimeConfig:
    """Runtime configuration management."""
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get configuration value."""
        from app.core.models import SystemConfiguration
        
        try:
            config = SystemConfiguration.objects.get(key=key, is_active=True)
            return config.value
        except SystemConfiguration.DoesNotExist:
            return default
    
    @staticmethod
    def set(key: str, value: Any, description: str = None) -> None:
        """Set configuration value."""
        from app.core.models import SystemConfiguration
        
        config, created = SystemConfiguration.objects.get_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'is_active': True
            }
        )
        
        if not created:
            config.value = value
            config.description = description or config.description
            config.save()

# Usage in application
maintenance_mode = RuntimeConfig.get('maintenance_mode', False)
max_upload_size = RuntimeConfig.get('max_upload_size', 10 * 1024 * 1024)  # 10MB
```

### Feature Flags

```python
# Feature flag system
class FeatureFlags:
    """Feature flag management."""
    
    @staticmethod
    def is_enabled(flag_name: str, user_id: str = None) -> bool:
        """Check if feature flag is enabled."""
        # Global flag check
        if RuntimeConfig.get(f'feature_flag_{flag_name}', False):
            return True
        
        # User-specific flag check
        if user_id:
            user_flags = RuntimeConfig.get(f'user_flags_{user_id}', {})
            return user_flags.get(flag_name, False)
        
        return False
    
    @staticmethod
    def enable_for_user(flag_name: str, user_id: str) -> None:
        """Enable feature flag for specific user."""
        user_flags = RuntimeConfig.get(f'user_flags_{user_id}', {})
        user_flags[flag_name] = True
        RuntimeConfig.set(f'user_flags_{user_id}', user_flags)

# Usage
if FeatureFlags.is_enabled('new_dashboard', request.user.id):
    # Show new dashboard
    pass
```

## Configuration Validation

### Startup Validation

```python
# Configuration validation at startup
class ConfigurationValidator:
    """Validate configuration at application startup."""
    
    @staticmethod
    def validate_required_settings():
        """Validate required settings are present."""
        required_settings = {
            'SECRET_KEY': 'Django secret key',
            'POSTGRES_DB': 'Database name',
            'POSTGRES_USER': 'Database user',
            'POSTGRES_PASSWORD': 'Database password',
        }
        
        missing = []
        for setting, description in required_settings.items():
            if not os.environ.get(setting):
                missing.append(f'{setting} ({description})')
        
        if missing:
            raise ValueError(f'Missing required settings: {", ".join(missing)}')
    
    @staticmethod
    def validate_database_connection():
        """Validate database connection."""
        from django.db import connection
        
        try:
            connection.ensure_connection()
        except Exception as e:
            raise ValueError(f'Database connection failed: {str(e)}')
    
    @staticmethod
    def validate_cache_connection():
        """Validate cache connection."""
        from django.core.cache import cache
        
        try:
            cache.set('config_test', 'ok', 10)
            if cache.get('config_test') != 'ok':
                raise ValueError('Cache write/read test failed')
        except Exception as e:
            raise ValueError(f'Cache connection failed: {str(e)}')
    
    @classmethod
    def run_all_validations(cls):
        """Run all configuration validations."""
        validations = [
            cls.validate_required_settings,
            cls.validate_database_connection,
            cls.validate_cache_connection,
        ]
        
        for validation in validations:
            try:
                validation()
            except ValueError as e:
                print(f'❌ Configuration validation failed: {e}')
                sys.exit(1)
        
        print('✅ Configuration validation passed')

# Run validation in settings
if not os.environ.get('SKIP_CONFIG_VALIDATION'):
    ConfigurationValidator.run_all_validations()
```

### Environment-Specific Validation

```python
# Production-specific validations
class ProductionValidator:
    """Additional validations for production environment."""
    
    @staticmethod
    def validate_security_settings():
        """Validate security settings for production."""
        security_checks = [
            ('DEBUG', False, 'Debug mode must be disabled'),
            ('SECRET_KEY', lambda x: x != 'change-me-in-production', 'Secret key must be changed'),
            ('SECURE_SSL_REDIRECT', True, 'SSL redirect must be enabled'),
            ('SESSION_COOKIE_SECURE', True, 'Secure session cookies required'),
            ('CSRF_COOKIE_SECURE', True, 'Secure CSRF cookies required'),
        ]
        
        for setting, expected, message in security_checks:
            value = globals().get(setting)
            
            if callable(expected):
                if not expected(value):
                    raise ValueError(f'{message}: {setting}={value}')
            elif value != expected:
                raise ValueError(f'{message}: {setting}={value}, expected {expected}')
    
    @staticmethod
    def validate_performance_settings():
        """Validate performance settings."""
        if not DATABASES['default'].get('CONN_MAX_AGE'):
            print('⚠️  Warning: Database connection pooling not configured')
        
        if CACHES['default']['TIMEOUT'] < 300:
            print('⚠️  Warning: Cache timeout is very low for production')

# Run production validations
if ENVIRONMENT == 'production':
    ProductionValidator.validate_security_settings()
    ProductionValidator.validate_performance_settings()
```

## Best Practices

### Configuration Organization

```python
# Organize settings by category
class DatabaseConfig:
    """Database configuration."""
    ENGINE = os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql')
    NAME = os.environ.get('POSTGRES_DB', 'django_app')
    USER = os.environ.get('POSTGRES_USER', 'postgres')
    PASSWORD = load_secret('POSTGRES_PASSWORD', '')
    HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    PORT = get_env_int('POSTGRES_PORT', 5432)

class CacheConfig:
    """Cache configuration."""
    BACKEND = 'django.core.cache.backends.memcached.PyMemcacheCache'
    LOCATION = get_env_list('MEMCACHED_SERVERS', ['memcached:11211'])
    TIMEOUT = get_env_int('CACHE_DEFAULT_TIMEOUT', 300)
    KEY_PREFIX = os.environ.get('CACHE_KEY_PREFIX', 'app')

class SecurityConfig:
    """Security configuration."""
    SECRET_KEY = load_secret('SECRET_KEY', 'change-me-in-production')
    SSL_REDIRECT = get_env_bool('SECURE_SSL_REDIRECT', False)
    HSTS_SECONDS = get_env_int('SECURE_HSTS_SECONDS', 31536000)

# Use in Django settings
DATABASES = {
    'default': {
        'ENGINE': DatabaseConfig.ENGINE,
        'NAME': DatabaseConfig.NAME,
        'USER': DatabaseConfig.USER,
        'PASSWORD': DatabaseConfig.PASSWORD,
        'HOST': DatabaseConfig.HOST,
        'PORT': DatabaseConfig.PORT,
    }
}
```

### Documentation

```python
# Self-documenting configuration
CONFIGURATION_DOCS = {
    'SECRET_KEY': {
        'description': 'Django secret key for cryptographic signing',
        'required': True,
        'type': 'string',
        'min_length': 50,
        'env_var': 'SECRET_KEY',
        'secret_file': '/run/secrets/SECRET_KEY',
    },
    'DEBUG': {
        'description': 'Enable debug mode (should be False in production)',
        'required': False,
        'type': 'boolean',
        'default': False,
        'env_var': 'DEBUG',
    },
    'POSTGRES_PASSWORD': {
        'description': 'PostgreSQL database password',
        'required': True,
        'type': 'string',
        'sensitive': True,
        'env_var': 'POSTGRES_PASSWORD',
        'secret_file': '/run/secrets/POSTGRES_PASSWORD',
    },
}

def generate_config_docs():
    """Generate configuration documentation."""
    for key, config in CONFIGURATION_DOCS.items():
        print(f"## {key}")
        print(f"**Description:** {config['description']}")
        print(f"**Required:** {config['required']}")
        print(f"**Type:** {config['type']}")
        
        if 'default' in config:
            print(f"**Default:** {config['default']}")
        
        if 'env_var' in config:
            print(f"**Environment Variable:** {config['env_var']}")
        
        if 'secret_file' in config:
            print(f"**Secret File:** {config['secret_file']}")
        
        print()
```

### Testing Configuration

```python
# Configuration for testing
class TestingConfig:
    """Testing-specific configuration overrides."""
    
    @staticmethod
    def override_for_testing():
        """Override settings for testing."""
        global DATABASES, CACHES, LOGGING
        
        # Use in-memory database for speed
        DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
        DATABASES['default']['NAME'] = ':memory:'
        
        # Use local memory cache
        CACHES['default']['BACKEND'] = 'django.core.cache.backends.locmem.LocMemCache'
        
        # Reduce logging verbosity
        LOGGING['root']['level'] = 'WARNING'
        
        # Disable migrations
        MIGRATION_MODULES = {app: None for app in LOCAL_APPS}

# Apply testing overrides
if ENVIRONMENT == 'testing':
    TestingConfig.override_for_testing()
```

---

This configuration system provides a robust, secure, and maintainable approach to managing application settings across different environments while following industry best practices.