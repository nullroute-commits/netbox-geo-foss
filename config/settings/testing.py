"""
Testing Django settings.
Settings for testing environment.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
from .base import *

# Testing environment
DEBUG = False
TESTING = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'web', 'testserver']

# Testing database settings
DATABASES['default'].update({
    'NAME': os.environ.get('POSTGRES_DB', 'django_app_test'),
})

# Use in-memory cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Disable migrations during testing for speed
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use faster password hasher for testing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Testing logging - reduce verbosity
LOGGING['handlers']['console']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['root']['level'] = 'WARNING'

# Disable HTTPS redirects for testing
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Testing-specific settings
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Disable audit logging during tests (unless specifically testing it)
AUDIT_ENABLED = os.environ.get('TEST_AUDIT_ENABLED', 'False').lower() == 'true'