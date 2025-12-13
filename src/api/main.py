"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from starlette.middleware.sessions import SessionMiddleware

from src.core.config import get_settings
from src.core.logging import setup_logging
from src.utils.health import router as health_router
from src.utils.version import get_version_info

# Initialize settings and logging
settings = get_settings()
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application", extra={
        "environment": settings.environment,
        "version": get_version_info()["version"],
    })

    # Initialize database
    # await init_database()

    # Initialize cache
    # await init_cache()

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Cleanup
    # await cleanup_database()
    # await cleanup_cache()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.example.com", "example.com"],
    )

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health_router, tags=["health"])

# Add more routers here
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
# app.include_router(items_router, prefix="/api/v1/items", tags=["items"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception": str(exc),
        },
        exc_info=True,
    )

    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/", response_model=dict[str, Any])
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if not settings.is_production else None,
    }


@app.get("/api/v1/version", response_model=dict[str, Any])
async def version() -> dict[str, Any]:
    """Get application version information."""
    return get_version_info()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        workers=settings.api_workers if not settings.is_development else 1,
        log_level=settings.log_level.lower(),
    )
