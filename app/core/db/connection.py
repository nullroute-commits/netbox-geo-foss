"""SQLAlchemy database connection configuration.

Provides database connectivity and session management for PostgreSQL 17.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
import os
import logging
from typing import Any, Dict, Optional
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# SQLAlchemy Base for model definitions
Base = declarative_base()

# Metadata for reflection and migrations
metadata = MetaData()

# Global engine and session factory
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


class DatabaseConnection:
    """
    Database connection manager using SQLAlchemy.

    Features:
    - Connection pooling
    - Health checks
    - Automatic reconnection
    - Performance monitoring
    - Transaction management
    """

    def __init__(self, database_url: Optional[str] = None, **kwargs):
        """
        Initialize database connection.

        Args:
            database_url: Database URL string
            **kwargs: Additional engine parameters
        """
        self.database_url = database_url or self._build_database_url()
        self.engine_params = {
            'poolclass': QueuePool,
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '3600')),
            'pool_pre_ping': True,
            'echo': os.environ.get('DB_ECHO', 'False').lower() == 'true',
            **kwargs
        }
        self.engine = None
        self.SessionLocal = None

    def _build_database_url(self) -> str:
        """
        Build database URL from environment variables.

        Returns:
            Database connection URL
        """
        user = os.environ.get('POSTGRES_USER', 'postgres')
        password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5432')
        database = os.environ.get('POSTGRES_DB', 'django_app')

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def connect(self) -> None:
        """
        Establish database connection and create session factory.

        Raises:
            Exception: If database connection fails
        """
        try:
            self.engine = create_engine(self.database_url, **self.engine_params)

            # Add event listeners
            event.listen(self.engine, "connect", self._on_connect)
            event.listen(self.engine, "checkout", self._on_checkout)

            # Test connection
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")

            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            logger.info(f"Connected to database: {self.database_url.split('@')[1]}")

        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def _on_connect(self, dbapi_connection, connection_record):
        """Handle new database connections."""
        logger.debug("New database connection established")

        # Set connection encoding
        if hasattr(dbapi_connection, 'set_client_encoding'):
            dbapi_connection.set_client_encoding('utf8')

    def _on_checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Handle connection checkout from pool."""
        logger.debug("Database connection checked out from pool")

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy session
        """
        if not self.SessionLocal:
            self.connect()

        return self.SessionLocal()

    def create_tables(self) -> None:
        """Create all tables defined in models."""
        if not self.engine:
            self.connect()

        Base.metadata.create_all(bind=self.engine)
        logger.info("Created database tables")

    def drop_tables(self) -> None:
        """Drop all tables defined in models."""
        if not self.engine:
            self.connect()

        Base.metadata.drop_all(bind=self.engine)
        logger.info("Dropped database tables")

    def health_check(self) -> bool:
        """
        Perform database health check.

        Returns:
            True if database is healthy, False otherwise
        """
        try:
            if not self.engine:
                self.connect()

            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                return result.scalar() == 1

        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get database connection information.

        Returns:
            Dictionary with connection details
        """
        if not self.engine:
            return {'status': 'disconnected'}

        pool = self.engine.pool
        return {
            'status': 'connected',
            'url': self.database_url.split('@')[1],  # Hide credentials
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
        }

    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Closed database connection")


# Global database connection instance
db_connection = DatabaseConnection()


def get_db_connection() -> DatabaseConnection:
    """
    Get the global database connection instance.

    Returns:
        DatabaseConnection instance
    """
    if not db_connection.engine:
        db_connection.connect()
    return db_connection


def get_db_session() -> Session:
    """
    Get a new database session.

    Returns:
        SQLAlchemy session
    """
    return get_db_connection().get_session()


def get_engine() -> Engine:
    """
    Get the SQLAlchemy engine.

    Returns:
        SQLAlchemy engine
    """
    connection = get_db_connection()
    return connection.engine


# Context manager for database sessions
class DatabaseSession:
    """
    Context manager for database sessions with automatic cleanup.

    Usage:
        with DatabaseSession() as session:
            # Use session
            pass
    """

    def __init__(self, auto_commit: bool = False):
        """
        Initialize database session context manager.

        Args:
            auto_commit: Whether to auto-commit on success
        """
        self.auto_commit = auto_commit
        self.session = None

    def __enter__(self) -> Session:
        """Enter context and return session."""
        self.session = get_db_session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup session."""
        if self.session:
            if exc_type is None and self.auto_commit:
                self.session.commit()
            elif exc_type is not None:
                self.session.rollback()

            self.session.close()


# Helper functions
def execute_raw_sql(sql: str, params: Optional[Dict] = None) -> Any:
    """
    Execute raw SQL query.

    Args:
        sql: SQL query string
        params: Query parameters

    Returns:
        Query result
    """
    with DatabaseSession() as session:
        return session.execute(sql, params or {}).fetchall()


def health_check() -> bool:
    """
    Perform database health check.

    Returns:
        True if database is healthy, False otherwise
    """
    return get_db_connection().health_check()
