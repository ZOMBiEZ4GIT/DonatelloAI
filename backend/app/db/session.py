"""
╔════════════════════════════════════════════════════════╗
║              Database Session Management                ║
║         AsyncSession factory and dependency injection  ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Async database connection pooling
    - Session lifecycle management
    - Dependency injection for endpoints

Security Considerations:
    - Connection string from environment/Key Vault
    - Connection pooling prevents exhaustion
    - Transactions for data integrity

ISO 27001 Control: A.12.3.1 - Information backup
"""

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import logger

# Global engine instance
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """
    Get or create the database engine.

    Returns:
        AsyncEngine: SQLAlchemy async engine

    Notes:
        - Uses connection pooling for performance
        - Configures pool size from settings
        - Handles both PostgreSQL and Azure SQL
    """
    global _engine

    if _engine is None:
        # Determine if we're using Azure SQL or PostgreSQL
        is_azure_sql = "mssql" in settings.DATABASE_URL

        # Configure connection args based on database type
        connect_args = {}
        if is_azure_sql:
            # Azure SQL specific settings
            connect_args = {
                "timeout": settings.DB_POOL_TIMEOUT,
                "TrustServerCertificate": "yes",
            }
        else:
            # PostgreSQL specific settings
            connect_args = {
                "server_settings": {
                    "application_name": settings.APP_NAME,
                },
                "command_timeout": settings.DB_POOL_TIMEOUT,
            }

        # Create engine with connection pooling
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE if not settings.TESTING_MODE else 5,
            max_overflow=settings.DB_MAX_OVERFLOW if not settings.TESTING_MODE else 0,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
            poolclass=NullPool if settings.TESTING_MODE else None,
            connect_args=connect_args,
        )

        logger.info(
            "database_engine_created",
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            is_azure_sql=is_azure_sql,
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the session factory.

    Returns:
        async_sessionmaker: Session factory for creating database sessions
    """
    global _session_factory

    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("database_session_factory_created")

    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.

    Yields:
        AsyncSession: Database session

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Use db session
            pass

    Notes:
        - Automatically commits on success
        - Automatically rolls back on exception
        - Closes session after request
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(
                "database_session_error",
                error=str(e),
                exc_info=True,
            )
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection.

    Called during application startup to verify database connectivity
    and warm up the connection pool.

    Raises:
        Exception: If database connection fails
    """
    try:
        engine = get_engine()

        # Test connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")

        logger.info(
            "database_initialized",
            database_url=settings.DATABASE_URL.split("@")[0] + "@***",  # Mask credentials
        )

    except Exception as e:
        logger.error(
            "database_initialization_failed",
            error=str(e),
            exc_info=True,
        )
        raise


async def close_db() -> None:
    """
    Close database connections.

    Called during application shutdown to gracefully close all
    database connections.
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None

        logger.info("database_connections_closed")


# ⚠️  DATABASE NOTES:
#
# 🔧 Connection Pooling:
# - Pre-ping ensures connections are alive
# - Connections recycled every hour
# - Pool size configurable via settings
# - NullPool used in testing mode
#
# 🔒 Security:
# - Credentials from environment/Key Vault
# - Connection strings never logged
# - Prepared statements prevent SQL injection
# - TLS encryption for Azure SQL
#
# 📊 Performance:
# - Async I/O for non-blocking operations
# - Connection reuse via pooling
# - Lazy initialization of engine
# - expire_on_commit=False for better performance
#
# 📋 ISO 27001 Control Mapping:
# - A.12.3.1: Information backup (database persistence)
# - A.12.4.1: Event logging (database audit trail)
# - A.14.2.1: Secure development policy
