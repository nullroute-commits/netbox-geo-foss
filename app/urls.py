"""URL configuration for the app module.

Basic URL patterns for the application.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
from django.urls import path
from django.http import JsonResponse

def home_view(request):
    """Render basic home view."""
    return JsonResponse({
        'message': 'Welcome to Django 5 Multi-Architecture CI/CD Pipeline',
        'status': 'running',
        'version': '1.0.0'
    })


urlpatterns = [
    path('', home_view, name='home'),
]
