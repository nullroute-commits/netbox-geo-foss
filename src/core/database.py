"""Database configuration and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings

settings = get_settings()

# Create async engine with database-specific parameters
engine_kwargs = {
    "echo": settings.database_echo,
    "pool_pre_ping": True,  # Enable connection health checks
}

# Only add pool parameters for PostgreSQL
if "postgres" in str(settings.database_url).lower():
    engine_kwargs.update(
        {
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
        }
    )

engine = create_async_engine(str(settings.database_url), **engine_kwargs)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize database."""
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)


async def cleanup_database() -> None:
    """Cleanup database connections."""
    await engine.dispose()
