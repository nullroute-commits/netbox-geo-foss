"""Version information utilities."""

import os
from datetime import datetime
from typing import Any

from src.core.config import get_settings

settings = get_settings()


def get_version_info() -> dict[str, Any]:
    """Get detailed version information."""
    return {
        "version": settings.app_version,
        "environment": settings.environment,
        "commit_sha": os.getenv("COMMIT_SHA", "unknown"),
        "build_date": os.getenv("BUILD_DATE", datetime.utcnow().isoformat()),
        "build_number": os.getenv("BUILD_NUMBER", "local"),
        "api_version": "v1",
    }
