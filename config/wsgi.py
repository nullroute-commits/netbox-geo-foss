"""
WSGI config for the application.
Exposes the WSGI callable as a module-level variable named 'application'.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_wsgi_application()