"""Health check endpoints."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from src.core.config import get_settings
from src.core.database import get_db

router = APIRouter()
settings = get_settings()


async def get_redis_client() -> redis.Redis:
    """Get Redis client."""
    return redis.from_url(str(settings.redis_url))


@router.get("/health", response_model=dict[str, Any])
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> dict[str, Any]:
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "environment": settings.environment,
        "checks": {
            "database": "unknown",
            "redis": "unknown",
        },
    }

    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        await redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
    finally:
        await redis_client.close()

    return health_status


@router.get("/ready", response_model=dict[str, bool])
async def readiness_check() -> dict[str, bool]:
    """Readiness check endpoint."""
    # Add any startup checks here
    return {"ready": True}


@router.get("/live", response_model=dict[str, bool])
async def liveness_check() -> dict[str, bool]:
    """Liveness check endpoint."""
    return {"alive": True}
